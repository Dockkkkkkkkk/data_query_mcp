1. 分析产品类别销售情况 (analyze_category_sales)
    - 功能：按产品类别统计销售总额、销售数量、平均价格和交易次数
    - SQL复杂度：使用JOIN连接表、GROUP BY分组、聚合函数
2. 热门产品分析 (get_top_products)
    - 功能：获取销售量最高的产品列表
    - 参数：可设置返回的产品数量(limit)
    - SQL复杂度：使用JOIN、GROUP BY、多个聚合函数
3. 销售趋势分析 (analyze_sales_trend)
    - 功能：分析不同时间段的销售趋势
    - 参数：时间分组方式(day/week/month/year)
    - SQL复杂度：使用DATE_FORMAT函数、GROUP BY按时间分组
4. 库存预警查询 (find_low_stock_products)
    - 功能：查找低于指定阈值的产品库存
    - 参数：库存阈值
    - SQL复杂度：使用子查询计算已售数量
5. 客户购买分析 (analyze_customer_purchases)
    - 功能：分析客户购买记录
    - 参数：客户名称(可选)
    - SQL复杂度：条件分支查询、子查询、GROUP_CONCAT函数、复杂聚合