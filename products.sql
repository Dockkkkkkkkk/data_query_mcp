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

 Date: 27/03/2025 16:37:23
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products`  (
  `product_id` int NOT NULL AUTO_INCREMENT,
  `product_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `price` decimal(10, 2) NOT NULL,
  `stock_quantity` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`product_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of products
-- ----------------------------
INSERT INTO `products` VALUES (1, '笔记本电脑', '电子产品', 5999.99, 50, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (2, '智能手机', '电子产品', 3999.99, 100, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (3, '无线耳机', '配件', 799.99, 200, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (4, '显示器', '电子产品', 1499.99, 30, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (5, '机械键盘', '配件', 499.99, 80, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (6, '游戏鼠标', '配件', 299.99, 120, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (7, '移动电源', '配件', 199.99, 150, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (8, '平板电脑', '电子产品', 2999.99, 60, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (9, '智能手表', '电子产品', 1299.99, 70, '2025-03-18 22:53:37');
INSERT INTO `products` VALUES (10, '蓝牙音箱', '电子产品', 599.99, 90, '2025-03-18 22:53:37');

SET FOREIGN_KEY_CHECKS = 1;
