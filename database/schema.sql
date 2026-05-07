-- SQL Schema for LLMRix SkillHub
-- Target: MySQL/MariaDB
-- Aligned with agent-team/db/mysql.sql

-- ----------------------------------------
-- Table: skill_info（技能主表）
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS `skill_info` (
  `id`          bigint        NOT NULL AUTO_INCREMENT        COMMENT '主键ID',
  `user_id`     bigint        DEFAULT NULL                   COMMENT '技能创建者ID',
  `skill_code`  varchar(64)   NOT NULL                       COMMENT '技能唯一标识',
  `skill_name`  varchar(128)  NOT NULL                       COMMENT '技能名称',
  `introduce`   varchar(1024) DEFAULT NULL                   COMMENT '技能介绍',
  `version`     int           NOT NULL DEFAULT '1'           COMMENT '当前最新版本号',
  `git_commit`  varchar(64)   DEFAULT NULL                   COMMENT '最新提交 commit hash',
  `git_path`    varchar(255)  DEFAULT NULL                   COMMENT 'Git 存储路径',
  `status`      tinyint       NOT NULL DEFAULT '0'           COMMENT '0-待审核 1-已上架 2-已下架',
  `category`    varchar(64)   DEFAULT NULL                   COMMENT '技能分类',
  `deleted`     tinyint       NOT NULL DEFAULT '0'           COMMENT '0-正常 1-已删除',
  `create_time` datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_skill_code` (`skill_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='技能信息表';

-- ----------------------------------------
-- Table: skill_version（技能版本历史表）
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS `skill_version` (
  `id`          bigint        NOT NULL AUTO_INCREMENT        COMMENT '主键ID',
  `skill_code`  varchar(64)   NOT NULL                       COMMENT '技能唯一标识',
  `version`     int           NOT NULL                       COMMENT '版本号',
  `git_commit`  varchar(64)   NOT NULL                       COMMENT '版本对应的 commit hash',
  `git_path`    varchar(255)  DEFAULT NULL                   COMMENT 'Git 存储路径',
  `user_id`     bigint        NOT NULL                       COMMENT '发布者用户ID',
  `introduce`   varchar(255)  DEFAULT NULL                   COMMENT '版本说明/提交信息',
  `deleted`     tinyint       NOT NULL DEFAULT '0'           COMMENT '0-正常 1-已删除',
  `create_time` datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_skill_version` (`skill_code`, `version`),
  KEY `idx_skill_code` (`skill_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='技能版本历史表';
