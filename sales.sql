/*
 Navicat Premium Data Transfer

 Source Server         : test_mcp
 Source Server Type    : MySQL
 Source Server Version : 80036
 Source Host           : 106.52.63.55:3306
 Source Schema         : test_mcp

 Target Server Type    : MySQL
 Target Server Version : 80036
 File Encoding         : 65001

 Date: 27/03/2025 16:37:34
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for sales
-- ----------------------------
DROP TABLE IF EXISTS `sales`;
CREATE TABLE `sales`  (
  `sale_id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `quantity` int NOT NULL,
  `total_price` decimal(10, 2) NOT NULL,
  `sale_date` date NOT NULL,
  `customer_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `salesperson` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`sale_id`) USING BTREE,
  INDEX `product_id`(`product_id` ASC) USING BTREE,
  CONSTRAINT `sales_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 31 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sales
-- ----------------------------
INSERT INTO `sales` VALUES (1, 1, 2, 11999.98, '2025-03-17', '张三', '张明');
INSERT INTO `sales` VALUES (2, 2, 5, 19999.95, '2025-03-16', '李四', '李军');
INSERT INTO `sales` VALUES (3, 3, 10, 7999.90, '2025-03-15', '王五', '王芳');
INSERT INTO `sales` VALUES (4, 4, 3, 4499.97, '2025-03-14', '赵六', '赵强');
INSERT INTO `sales` VALUES (5, 5, 4, 1999.96, '2025-03-13', '钱七', '张明');
INSERT INTO `sales` VALUES (6, 6, 8, 2399.92, '2025-03-12', '孙八', '李军');
INSERT INTO `sales` VALUES (7, 7, 15, 2999.85, '2025-03-11', '周九', '王芳');
INSERT INTO `sales` VALUES (8, 8, 2, 5999.98, '2025-03-10', '吴十', '赵强');
INSERT INTO `sales` VALUES (9, 9, 3, 3899.97, '2025-03-09', '郑十一', '张明');
INSERT INTO `sales` VALUES (10, 10, 5, 2999.95, '2025-03-08', '王十二', '李军');
INSERT INTO `sales` VALUES (11, 1, 1, 5999.99, '2025-03-07', '李十三', '王芳');
INSERT INTO `sales` VALUES (12, 2, 2, 7999.98, '2025-03-06', '张十四', '赵强');
INSERT INTO `sales` VALUES (13, 3, 5, 3999.95, '2025-03-05', '刘十五', '张明');
INSERT INTO `sales` VALUES (14, 4, 1, 1499.99, '2025-03-04', '陈十六', '李军');
INSERT INTO `sales` VALUES (15, 5, 3, 1499.97, '2025-03-03', '杨十七', '王芳');
INSERT INTO `sales` VALUES (16, 6, 4, 1199.96, '2025-03-02', '赵十八', '赵强');
INSERT INTO `sales` VALUES (17, 7, 10, 1999.90, '2025-03-01', '孙十九', '张明');
INSERT INTO `sales` VALUES (18, 8, 1, 2999.99, '2025-02-28', '周二十', '李军');
INSERT INTO `sales` VALUES (19, 9, 2, 2599.98, '2025-02-27', '吴二十一', '王芳');
INSERT INTO `sales` VALUES (20, 10, 3, 1799.97, '2025-02-26', '郑二十二', '赵强');
INSERT INTO `sales` VALUES (21, 1, 1, 5999.99, '2025-02-25', '王二十三', '张明');
INSERT INTO `sales` VALUES (22, 2, 1, 3999.99, '2025-02-24', '李二十四', '李军');
INSERT INTO `sales` VALUES (23, 3, 2, 1599.98, '2025-02-23', '张二十五', '王芳');
INSERT INTO `sales` VALUES (24, 4, 2, 2999.98, '2025-02-22', '刘二十六', '赵强');
INSERT INTO `sales` VALUES (25, 5, 5, 2499.95, '2025-02-21', '陈二十七', '张明');
INSERT INTO `sales` VALUES (26, 6, 3, 899.97, '2025-02-20', '杨二十八', '李军');
INSERT INTO `sales` VALUES (27, 7, 8, 1599.92, '2025-02-19', '赵二十九', '王芳');
INSERT INTO `sales` VALUES (28, 8, 1, 2999.99, '2025-02-18', '孙三十', '赵强');
INSERT INTO `sales` VALUES (29, 9, 1, 1299.99, '2025-02-17', '周三十一', '张明');
INSERT INTO `sales` VALUES (30, 10, 2, 1199.98, '2025-02-16', '吴三十二', '李军');

SET FOREIGN_KEY_CHECKS = 1;
