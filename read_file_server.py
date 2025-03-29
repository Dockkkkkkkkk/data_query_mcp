"""
MCP服务器 - Excel文件读取器
提供通过路径读取Windows本地Excel文件的功能
"""
import os
import sys
import json
import asyncio
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List, Union
from fastapi import FastAPI, HTTPException

# 导入MCP服务器库
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult

# server = FastMCP(name="mysql-server", description="MySQL数据库交互服务器")

# 创建MCP服务器实例
mcp = FastMCP("Excel文件读取器")

@mcp.tool(description="读取Excel文件内容")
async def read_excel_file(file_path: str, sheet_name: Optional[Union[str, int]] = 0, nrows: Optional[int] = None) -> Dict[str, Any]:
    """
    读取指定路径的Excel文件，可选择特定的工作表和行数
    
    Args:
        file_path: Excel文件的路径（绝对路径或相对路径）
        sheet_name: 要读取的工作表名称或索引，默认为第一个工作表
        nrows: 要读取的最大行数，默认读取所有行
    
    Returns:
        包含Excel数据和元信息的字典
    """
    try:
        # 确保文件路径存在
        if not os.path.exists(file_path):
            return {
                "error": f"文件不存在: {file_path}",
                "current_directory": os.getcwd(),
                "file_exists": False
            }
        
        # 确保文件是Excel文件
        if not file_path.endswith(('.xls', '.xlsx', '.xlsm', '.xlsb')):
            return {
                "error": f"文件不是Excel格式: {file_path}",
                "file_exists": True
            }
        
        # 读取Excel文件
        read_params = {}
        if nrows is not None:
            read_params['nrows'] = nrows
        
        # 尝试读取所有sheet信息
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        
        # 读取指定的sheet
        df = pd.read_excel(file_path, sheet_name=sheet_name, **read_params)
        
        # 转换DataFrame为字典
        if isinstance(df, pd.DataFrame):
            data = df.to_dict(orient='records')
            columns = df.columns.tolist()
            # 获取基本统计信息
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            stats = {}
            for col in numeric_columns:
                stats[col] = {
                    "min": df[col].min() if not df[col].empty else None,
                    "max": df[col].max() if not df[col].empty else None,
                    "mean": df[col].mean() if not df[col].empty else None,
                    "median": df[col].median() if not df[col].empty else None
                }
            
            return {
                "success": True,
                "file_path": file_path,
                "sheet_name": sheet_name,
                "sheet_names": sheet_names,
                "total_sheets": len(sheet_names),
                "rows": len(df),
                "columns": columns,
                "column_count": len(columns),
                "data": data[:100],  # 限制返回的数据量
                "data_preview": df.head(10).to_string(),
                "statistics": stats
            }
        else:
            # 如果sheet_name=None，返回多个工作表的信息
            result = {
                "success": True,
                "file_path": file_path,
                "total_sheets": len(df),
                "sheet_info": {}
            }
            for sheet, sheet_df in df.items():
                result["sheet_info"][sheet] = {
                    "rows": len(sheet_df),
                    "columns": sheet_df.columns.tolist(),
                    "column_count": len(sheet_df.columns),
                    "preview": sheet_df.head(5).to_string()
                }
            return result
            
    except Exception as e:
        return {
            "error": str(e),
            "file_path": file_path,
            "exception_type": type(e).__name__
        }

@mcp.tool(description="获取Excel文件的工作表列表")
async def list_excel_sheets(file_path: str) -> Dict[str, Any]:
    """
    获取Excel文件中的所有工作表名称
    
    Args:
        file_path: Excel文件的路径
    
    Returns:
        包含工作表列表的字典
    """
    try:
        if not os.path.exists(file_path):
            return {
                "error": f"文件不存在: {file_path}",
                "current_directory": os.getcwd()
            }
        
        # 读取Excel文件工作表信息
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        
        # 获取每个工作表的基本信息
        sheet_info = {}
        for sheet in sheet_names:
            # 读取前几行以获取列信息
            df_preview = pd.read_excel(file_path, sheet_name=sheet, nrows=1)
            sheet_info[sheet] = {
                "columns": df_preview.columns.tolist(),
                "column_count": len(df_preview.columns)
            }
        
        return {
            "success": True,
            "file_path": file_path,
            "sheet_names": sheet_names,
            "total_sheets": len(sheet_names),
            "sheet_info": sheet_info
        }
    except Exception as e:
        return {
            "error": str(e),
            "file_path": file_path
        }

@mcp.tool(description="查询Excel数据")
async def query_excel_data(file_path: str, sheet_name: Optional[Union[str, int]] = 0, query: str = "") -> Dict[str, Any]:
    """
    对Excel数据执行简单的查询操作
    
    Args:
        file_path: Excel文件的路径
        sheet_name: 要查询的工作表名称或索引
        query: 查询字符串，使用pandas query语法
    
    Returns:
        查询结果
    """
    try:
        if not os.path.exists(file_path):
            return {
                "error": f"文件不存在: {file_path}"
            }
        
        # 读取Excel文件
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 如果提供了查询，执行查询
        if query:
            try:
                result_df = df.query(query)
                return {
                    "success": True,
                    "file_path": file_path,
                    "sheet_name": sheet_name,
                    "query": query,
                    "rows_before_query": len(df),
                    "rows_after_query": len(result_df),
                    "data": result_df.to_dict(orient='records')[:100],
                    "preview": result_df.head(10).to_string()
                }
            except Exception as query_err:
                return {
                    "error": f"查询执行失败: {str(query_err)}",
                    "query": query
                }
        else:
            return {
                "success": True,
                "message": "未提供查询字符串，返回表格信息",
                "file_path": file_path,
                "sheet_name": sheet_name,
                "rows": len(df),
                "columns": df.columns.tolist(),
                "column_count": len(df.columns),
                "preview": df.head(5).to_string()
            }
    except Exception as e:
        return {
            "error": str(e),
            "file_path": file_path
        }

@mcp.resource("excel://{file_path}")
async def excel_resource(file_path: str) -> Tuple[str, str]:
    """
    提供Excel文件的基本信息作为资源
    
    Args:
        file_path: Excel文件的路径
    
    Returns:
        包含Excel文件信息的文本和MIME类型
    """
    try:
        if not os.path.exists(file_path):
            return json.dumps({
                "error": f"文件不存在: {file_path}",
                "current_directory": os.getcwd()
            }), "application/json"
        
        # 获取文件基本信息
        file_info = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "last_modified": os.path.getmtime(file_path)
        }
        
        # 读取Excel文件基本信息
        xl = pd.ExcelFile(file_path)
        file_info["sheet_names"] = xl.sheet_names
        file_info["total_sheets"] = len(xl.sheet_names)
        
        return json.dumps(file_info), "application/json"
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "file_path": file_path
        }), "application/json"

@mcp.prompt(description="分析Excel文件")
async def analyze_excel_prompt(file_path: str) -> str:
    """
    创建一个用于分析Excel文件的提示
    
    Args:
        file_path: Excel文件的路径
    
    Returns:
        用于指导模型分析Excel文件的提示文本
    """
    prompt = f"""
    请分析位于 {file_path} 的Excel文件。
    
    你可以执行以下操作：
    1. 使用 read_excel_file 工具读取文件内容
    2. 使用 list_excel_sheets 工具获取所有工作表的列表
    3. 使用 query_excel_data 工具对数据进行查询
    
    首先，请列出文件中的所有工作表，然后分析每个工作表的数据结构和内容。
    你可以生成统计摘要、识别数据趋势，并根据数据特征提供洞察和建议。
    """
    return prompt

# async def main():
#     # 启动MCP服务器
#     async with stdio_server(mcp):
#         # 服务器将在上下文管理器内运行
#         # 当上下文退出时，服务器会自动关闭
#         await asyncio.Future()  # 保持服务器运行，直到外部终止

if __name__ == "__main__":
    mcp.run(transport='stdio')
