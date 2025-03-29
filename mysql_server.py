"""
MySQL数据库MCP服务器
提供与MySQL数据库交互的通用工具和提示模板
"""
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from mcp.server.fastmcp import FastMCP

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger('mysql_mcp_server')

# 从环境变量获取数据库连接配置
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "demo"),
    "charset": 'utf8mb4',
    "use_unicode": True,
    "get_warnings": True
}

logger.info(f"从环境变量加载数据库配置: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

# 初始化MCP服务器
server = FastMCP(name="mysql-server", description="MySQL数据库交互服务器")

def get_db_connection():
    """创建并返回数据库连接"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"数据库连接错误: {str(e)}")
        return None

def json_serialize(obj):
    """处理特殊类型的JSON序列化"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif hasattr(obj, 'decimal') or str(type(obj)) == "<class 'decimal.Decimal'>":
        # 处理Decimal类型
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# ======= 数据库工具 =======

@server.tool()
async def execute_query(query: str) -> Dict[str, Any]:
    """执行SQL查询并返回结果
    
    Args:
        query: SQL查询语句
        
    Returns:
        查询结果或错误信息
    """
    try:
        logger.info(f"执行SQL查询: {query}")
        conn = get_db_connection()
        if not conn:
            logger.error("数据库连接失败")
            return {"error": "无法连接到数据库"}
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        
        # 检查是否是SELECT查询
        if query.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE")):
            results = cursor.fetchall()
            logger.debug(f"查询返回 {len(results)} 条结果")
            try:
                # 确保结果是可JSON序列化的
                serializable_results = json.loads(
                    json.dumps(results[:1000], default=json_serialize)
                )
                logger.info("成功序列化查询结果")
                return {
                    "success": True,
                    "query_type": "SELECT",
                    "row_count": len(results),
                    "results": serializable_results
                }
            except Exception as e:
                logger.error(f"JSON序列化失败: {str(e)}")
                return {"error": f"结果序列化失败: {str(e)}"}
        else:
            # 对于INSERT, UPDATE, DELETE等查询
            conn.commit()
            logger.info(f"更新操作影响了 {cursor.rowcount} 行")
            return {
                "success": True,
                "query_type": "UPDATE",
                "affected_rows": cursor.rowcount,
                "message": f"查询执行成功，影响了{cursor.rowcount}行"
            }
    except Exception as e:
        logger.error(f"查询执行失败: {str(e)}")
        return {"error": str(e)}
    finally:
        if 'conn' in locals() and conn is not None and conn.is_connected():
            cursor.close()
            conn.close()
            logger.debug("数据库连接已关闭")

@server.tool()
async def get_tables() -> Dict[str, Any]:
    """获取数据库中的所有表
    
    Returns:
        表列表及其行数和结构
    """
    try:
        logger.info("获取所有表信息")
        # 执行查询获取所有表
        tables_result = await execute_query("SHOW TABLES")
        
        if "error" in tables_result:
            logger.error(f"获取表列表失败: {tables_result['error']}")
            return tables_result
            
        tables = []
        for table_row in tables_result["results"]:
            table_name = list(table_row.values())[0]
            logger.debug(f"处理表: {table_name}")
            
            # 获取表的行数
            count_result = await execute_query(f"SELECT COUNT(*) as count FROM `{table_name}`")
            row_count = 0
            if "error" not in count_result and count_result["results"]:
                row_count = count_result["results"][0]["count"]
                
            # 获取表结构
            structure_result = await execute_query(f"DESCRIBE `{table_name}`")
            structure = structure_result.get("results", []) if "error" not in structure_result else []
            
            try:
                # 确保数据是可JSON序列化的
                serializable_structure = json.loads(
                    json.dumps(structure, default=json_serialize)
                )
                logger.debug(f"表 {table_name} 结构序列化成功")
                    
                tables.append({
                    "name": table_name,
                    "row_count": row_count,
                    "structure": serializable_structure
                })
            except Exception as e:
                logger.error(f"表 {table_name} 结构序列化失败: {str(e)}")
                return {"error": f"表结构序列化失败: {str(e)}"}
            
        logger.info(f"成功获取 {len(tables)} 个表的信息")
        return {
            "success": True,
            "database": DB_CONFIG["database"],
            "table_count": len(tables),
            "tables": tables
        }
    except Exception as e:
        logger.error(f"获取表信息失败: {str(e)}")
        return {"error": str(e)}

@server.tool()
async def visualize_data(query: str, x_column: str, y_column: str, chart_type: str = "bar") -> Dict[str, Any]:
    """执行查询并可视化结果
    
    Args:
        query: SQL查询语句
        x_column: X轴列名
        y_column: Y轴列名
        chart_type: 图表类型 (bar, line, scatter, pie)
        
    Returns:
        包含Base64编码图表的结果
    """
    try:
        # 执行查询
        query_result = await execute_query(query)
        
        if "error" in query_result:
            return query_result
            
        if not query_result.get("results"):
            return {"error": "查询没有返回结果"}
            
        # 将结果转换为DataFrame
        df = pd.DataFrame(query_result["results"])
        
        # 检查列是否存在
        if x_column not in df.columns:
            return {"error": f"列 '{x_column}' 不在结果中"}
            
        if y_column not in df.columns:
            return {"error": f"列 '{y_column}' 不在结果中"}
            
        # 创建图表
        plt.figure(figsize=(10, 6))
        
        if chart_type == "bar":
            plt.bar(df[x_column], df[y_column])
            plt.title(f"{y_column} by {x_column}")
        elif chart_type == "line":
            plt.plot(df[x_column], df[y_column], marker='o')
            plt.title(f"{y_column} vs {x_column}")
        elif chart_type == "scatter":
            plt.scatter(df[x_column], df[y_column])
            plt.title(f"{y_column} vs {x_column} (Scatter)")
        elif chart_type == "pie":
            # 饼图需要正的值
            if (df[y_column] < 0).any():
                return {"error": "饼图不能包含负值"}
                
            plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%')
            plt.title(f"Distribution of {y_column}")
        else:
            return {"error": f"不支持的图表类型: {chart_type}"}
            
        plt.xlabel(x_column)
        plt.ylabel(y_column)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 将图表转换为Base64字符串
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return {
            "success": True,
            "chart_type": chart_type,
            "x_column": x_column,
            "y_column": y_column,
            "row_count": len(df),
            "chart_image": image_base64
        }
    except Exception as e:
        logger.error(f"可视化数据失败: {str(e)}")
        return {"error": str(e)}

@server.tool()
async def show_tables_info() -> Dict[str, Any]:
    """获取数据库中的所有表及其结构信息
    
    Returns:
        包含所有表及其结构的字典
    """
    try:
        logger.info("获取数据库表结构信息")
        
        # 获取所有表
        tables_result = await execute_query("SHOW TABLES")
        if "error" in tables_result:
            return tables_result
            
        tables_info = []
        
        for table_row in tables_result["results"]:
            table_name = list(table_row.values())[0]
            logger.info(f"获取表 {table_name} 的结构")
            
            # 获取表结构
            structure_result = await execute_query(f"DESCRIBE `{table_name}`")
            if "error" not in structure_result:
                structure = structure_result.get("results", [])
                
                # 获取表行数
                count_result = await execute_query(f"SELECT COUNT(*) as count FROM `{table_name}`")
                row_count = 0
                if "error" not in count_result and count_result.get("results"):
                    row_count = count_result["results"][0]["count"]
                
                # 获取表前5条数据作为示例
                sample_result = await execute_query(f"SELECT * FROM `{table_name}` LIMIT 5")
                samples = []
                if "error" not in sample_result:
                    samples = sample_result.get("results", [])
                
                tables_info.append({
                    "name": table_name,
                    "row_count": row_count,
                    "structure": structure,
                    "sample_data": samples
                })
            
        return {
            "success": True,
            "database": DB_CONFIG["database"],
            "tables_count": len(tables_info),
            "tables": tables_info
        }
    except Exception as e:
        logger.error(f"获取表结构信息失败: {str(e)}")
        return {"error": str(e)}

@server.tool()
async def get_table_columns(table_name: str) -> Dict[str, Any]:
    """获取指定表的列信息
    
    Args:
        table_name: 表名
        
    Returns:
        表列信息
    """
    try:
        logger.info(f"获取表 {table_name} 的列信息")
        
        # 检查表是否存在
        tables_result = await execute_query("SHOW TABLES")
        if "error" in tables_result:
            return tables_result
            
        table_exists = False
        for table_row in tables_result["results"]:
            if table_name == list(table_row.values())[0]:
                table_exists = True
                break
                
        if not table_exists:
            return {"error": f"表 '{table_name}' 不存在"}
            
        # 获取表结构
        structure_result = await execute_query(f"DESCRIBE `{table_name}`")
        if "error" in structure_result:
            return structure_result
            
        columns = structure_result.get("results", [])
        
        return {
            "success": True,
            "table": table_name,
            "columns_count": len(columns),
            "columns": columns
        }
    except Exception as e:
        logger.error(f"获取表列信息失败: {str(e)}")
        return {"error": str(e)}
    
    
    

@server.tool()
async def analyze_category_sales() -> Dict[str, Any]:
    """分析每个产品类别的销售情况
    
    Returns:
        按类别统计的销售数据，包括销售总额、销售数量和平均价格
    """
    try:
        logger.info("分析各产品类别的销售情况")
        
        query = """
        SELECT 
            p.category,
            SUM(s.total_price) AS total_sales_amount,
            SUM(s.quantity) AS total_sales_quantity,
            AVG(p.price) AS average_price,
            COUNT(DISTINCT s.sale_id) AS transaction_count
        FROM products p
        JOIN sales s ON p.product_id = s.product_id
        GROUP BY p.category
        ORDER BY total_sales_amount DESC
        """
        
        result = await execute_query(query)
        
        if "error" in result:
            return result
            
        return {
            "success": True,
            "analysis_type": "category_sales",
            "results": result.get("results", []),
            "description": "按产品类别统计的销售数据"
        }
    except Exception as e:
        logger.error(f"分析类别销售失败: {str(e)}")
        return {"error": str(e)}

@server.tool()
async def get_top_products(limit: int = 10) -> Dict[str, Any]:
    """获取销售量最高的产品
    
    Args:
        limit: 要返回的产品数量
        
    Returns:
        销售量最高的产品列表
    """
    try:
        logger.info(f"获取销售量最高的{limit}个产品")
        
        query = f"""
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            p.price,
            SUM(s.quantity) AS total_quantity_sold,
            SUM(s.total_price) AS total_revenue,
            COUNT(DISTINCT s.sale_id) AS sale_count
        FROM products p
        JOIN sales s ON p.product_id = s.product_id
        GROUP BY p.product_id, p.product_name, p.category, p.price
        ORDER BY total_quantity_sold DESC
        LIMIT {limit}
        """
        
        result = await execute_query(query)
        
        if "error" in result:
            return result
            
        return {
            "success": True,
            "analysis_type": "top_products",
            "limit": limit,
            "results": result.get("results", []),
            "description": f"销售量最高的{limit}个产品"
        }
    except Exception as e:
        logger.error(f"获取热门产品失败: {str(e)}")
        return {"error": str(e)}

@server.tool()
async def analyze_sales_trend(group_by: str = 'month') -> Dict[str, Any]:
    """分析销售趋势
    
    Args:
        group_by: 分组类型，可选值有: 'day', 'week', 'month', 'year'
        
    Returns:
        按时间段统计的销售数据
    """
    try:
        logger.info(f"分析销售趋势，按{group_by}分组")
        
        # 根据分组类型构建不同的查询
        time_format = {
            'day': '%Y-%m-%d',
            'week': '%Y-%u',  # ISO周，格式为YYYY-WW
            'month': '%Y-%m',
            'year': '%Y'
        }
        
        if group_by not in time_format:
            return {"error": f"不支持的分组类型: {group_by}，支持的类型有: 'day', 'week', 'month', 'year'"}
            
        query = f"""
        SELECT 
            DATE_FORMAT(s.sale_date, '{time_format[group_by]}') AS time_period,
            SUM(s.total_price) AS total_sales,
            SUM(s.quantity) AS total_quantity,
            COUNT(DISTINCT s.sale_id) AS order_count,
            COUNT(DISTINCT s.product_id) AS product_count,
            AVG(s.total_price / s.quantity) AS average_unit_price
        FROM sales s
        GROUP BY time_period
        ORDER BY time_period
        """
        
        result = await execute_query(query)
        
        if "error" in result:
            return result
            
        return {
            "success": True,
            "analysis_type": "sales_trend",
            "group_by": group_by,
            "results": result.get("results", []),
            "description": f"按{group_by}分析的销售趋势"
        }
    except Exception as e:
        logger.error(f"分析销售趋势失败: {str(e)}")
        return {"error": str(e)}

@server.tool()
async def find_low_stock_products(threshold: int = 10) -> Dict[str, Any]:
    """查找库存低于阈值的产品
    
    Args:
        threshold: 库存阈值
        
    Returns:
        库存低于阈值的产品列表
    """
    try:
        logger.info(f"查找库存低于{threshold}的产品")
        
        query = f"""
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            p.price,
            p.stock_quantity,
            (SELECT SUM(quantity) FROM sales s WHERE s.product_id = p.product_id) AS total_sold,
            p.created_at
        FROM products p
        WHERE p.stock_quantity < {threshold}
        ORDER BY p.stock_quantity ASC
        """
        
        result = await execute_query(query)
        
        if "error" in result:
            return result
            
        return {
            "success": True,
            "analysis_type": "low_stock_products",
            "threshold": threshold,
            "results": result.get("results", []),
            "description": f"库存低于{threshold}的产品列表"
        }
    except Exception as e:
        logger.error(f"查找低库存产品失败: {str(e)}")
        return {"error": str(e)}

@server.tool()
async def analyze_customer_purchases(customer_name: str = None) -> Dict[str, Any]:
    """分析客户购买记录
    
    Args:
        customer_name: 客户名称，如果不提供则分析所有客户
        
    Returns:
        客户购买记录分析
    """
    try:
        logger.info(f"分析{'特定客户' if customer_name else '所有客户'}的购买记录")
        
        # 构建基本查询
        if customer_name:
            # 分析指定客户的购买记录
            query = f"""
            SELECT 
                s.customer_name,
                COUNT(DISTINCT s.sale_id) AS total_orders,
                SUM(s.quantity) AS total_items_purchased,
                SUM(s.total_price) AS total_spent,
                AVG(s.total_price) AS average_order_value,
                MIN(s.sale_date) AS first_purchase_date,
                MAX(s.sale_date) AS last_purchase_date,
                DATEDIFF(MAX(s.sale_date), MIN(s.sale_date)) AS customer_lifespan_days,
                GROUP_CONCAT(DISTINCT p.category ORDER BY p.category SEPARATOR ', ') AS purchased_categories,
                (
                    SELECT p2.product_name 
                    FROM sales s2 
                    JOIN products p2 ON s2.product_id = p2.product_id 
                    WHERE s2.customer_name = s.customer_name 
                    GROUP BY p2.product_id 
                    ORDER BY SUM(s2.quantity) DESC 
                    LIMIT 1
                ) AS favorite_product
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            WHERE s.customer_name = '{customer_name}'
            GROUP BY s.customer_name
            """
            
            # 获取该客户的购买详情
            details_query = f"""
            SELECT 
                s.sale_id,
                s.sale_date,
                p.product_name,
                p.category,
                s.quantity,
                s.total_price,
                s.salesperson
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            WHERE s.customer_name = '{customer_name}'
            ORDER BY s.sale_date DESC
            """
            
            result = await execute_query(query)
            details_result = await execute_query(details_query)
            
            if "error" in result:
                return result
                
            return {
                "success": True,
                "analysis_type": "customer_purchases",
                "customer_name": customer_name,
                "summary": result.get("results", []),
                "purchase_details": details_result.get("results", []),
                "description": f"客户'{customer_name}'的购买记录分析"
            }
        else:
            # 分析所有客户
            query = """
            SELECT 
                s.customer_name,
                COUNT(DISTINCT s.sale_id) AS total_orders,
                SUM(s.quantity) AS total_items_purchased,
                SUM(s.total_price) AS total_spent,
                AVG(s.total_price) AS average_order_value,
                MIN(s.sale_date) AS first_purchase_date,
                MAX(s.sale_date) AS last_purchase_date
            FROM sales s
            WHERE s.customer_name IS NOT NULL
            GROUP BY s.customer_name
            ORDER BY total_spent DESC
            """
            
            result = await execute_query(query)
            
            if "error" in result:
                return result
                
            return {
                "success": True,
                "analysis_type": "all_customers_purchases",
                "results": result.get("results", []),
                "description": "所有客户的购买记录分析"
            }
    except Exception as e:
        logger.error(f"分析客户购买记录失败: {str(e)}")
        return {"error": str(e)}

# ======= 提示模板 =======

@server.prompt()
def sql_query_builder() -> str:
    """SQL查询构建器提示模板"""
    return """
请帮我构建一个SQL查询来从数据库中检索信息。

数据库当前包含以下表:
{tables_info}

我需要一个查询来解决以下问题:
{problem_description}

请提供完整的SQL查询，并解释查询的每个部分。
"""

@server.prompt()
def data_analysis_report() -> str:
    """数据分析报告生成提示模板"""
    return """
请基于以下数据生成一份详细的分析报告:

```
{data}
```

报告应包括:
1. 数据概述和主要指标
2. 关键趋势和模式分析
3. 异常值和特殊情况识别
4. 业务洞察和建议

请使用专业的语言和格式，使报告易于理解和实用。
"""

# ======= 资源 =======

@server.resource("mysql://schema/{table}")
async def get_table_schema(table: str) -> str:
    """获取表结构"""
    try:
        structure_result = await execute_query(f"DESCRIBE `{table}`")
        if "error" in structure_result:
            return f"Error: {structure_result['error']}"
            
        structure = structure_result.get("results", [])
        return json.dumps(structure, default=json_serialize, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@server.resource("mysql://data/{table}")
async def get_table_data(table: str) -> str:
    """获取表数据"""
    try:
        data_result = await execute_query(f"SELECT * FROM `{table}` LIMIT 50")
        if "error" in data_result:
            return f"Error: {data_result['error']}"
            
        data = data_result.get("results", [])
        return json.dumps(data, default=json_serialize, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@server.resource("mysql://info")
async def get_database_info() -> str:
    """获取数据库信息"""
    try:
        # 获取数据库版本
        version_result = await execute_query("SELECT VERSION() as version")
        if "error" in version_result:
            return f"Error: {version_result['error']}"
            
        version = version_result.get("results", [{}])[0].get("version", "Unknown")
        
        # 获取数据库状态
        status_result = await execute_query("SHOW STATUS")
        if "error" in status_result:
            status = []
        else:
            status = status_result.get("results", [])
            
        # 获取所有表
        tables_info = await get_tables()
        if "error" in tables_info:
            tables = []
        else:
            tables = tables_info.get("tables", [])
            
        info = {
            "database": DB_CONFIG["database"],
            "version": version,
            "host": DB_CONFIG["host"],
            "tables": [table["name"] for table in tables],
            "table_count": len(tables)
        }
        
        return json.dumps(info, default=json_serialize, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

# 启动服务器
if __name__ == "__main__":
    logger.info("启动MySQL数据库MCP服务器...")
    logger.info(f"数据库配置: {DB_CONFIG}")
    logger.info("使用stdio传输方式")
    
    try:
        server.run(transport='stdio')
    
    except Exception as e:
        logger.error(f"服务器运行失败: {str(e)}")
        sys.exit(1) 