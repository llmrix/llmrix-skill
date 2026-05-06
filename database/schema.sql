-- SQL Schema for LLMRix SkillHub
-- Target: MySQL/MariaDB

CREATE TABLE IF NOT EXISTS `skill_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL COMMENT 'Owner/Creator ID',
  `skill_code` varchar(64) NOT NULL COMMENT 'Unique identifier (e.g., pdf_converter)',
  `name` varchar(128) NOT NULL COMMENT 'Display name',
  `version` int(11) DEFAULT '1' COMMENT 'Current version number',
  `description` text COMMENT 'Skill description',
  `category` varchar(64) DEFAULT NULL COMMENT 'Skill category',
  `commit_hash` varchar(64) DEFAULT NULL COMMENT 'Git commit hash of current version',
  `file_path` varchar(255) DEFAULT NULL COMMENT 'Relative path in git repo',
  `status` int(11) DEFAULT '0' COMMENT '0: active, 1: disabled',
  `deleted` tinyint(1) DEFAULT '0',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_skill_code` (`skill_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Skill Information';

CREATE TABLE IF NOT EXISTS `skill_version` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `skill_code` varchar(64) NOT NULL,
  `version` int(11) NOT NULL,
  `commit_hash` varchar(64) NOT NULL,
  `author_id` int(11) DEFAULT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  `message` varchar(255) DEFAULT NULL COMMENT 'Commit/Release message',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_skill_code_version` (`skill_code`, `version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Skill Version History';
