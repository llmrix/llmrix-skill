-- =============================================================================
-- skill_info — 技能信息表
-- =============================================================================

CREATE TABLE IF NOT EXISTS skill_info (
    id          BIGSERIAL       PRIMARY KEY,                    -- 自增主键
    user_id     BIGINT          DEFAULT NULL,             -- 所属用户 ID（null=全局）
    skill_code  VARCHAR(64)     NOT NULL,                 -- 技能唯一编码
    skill_name  VARCHAR(128)    NOT NULL,                 -- 技能名称
    introduce   VARCHAR(1024)   DEFAULT NULL,             -- 技能简介
    version     INT             NOT NULL DEFAULT 1,       -- 当前版本号
    git_commit  VARCHAR(64)     DEFAULT NULL,             -- 版本提交 hash
    git_path    VARCHAR(255)    DEFAULT NULL,             -- 仓库路径
    status      SMALLINT        NOT NULL DEFAULT 0,       -- 0=下架 1=上架
    category    VARCHAR(64)     DEFAULT NULL,             -- 技能分类
    deleted     SMALLINT        NOT NULL DEFAULT 0,       -- 软删除：0=正常 1=已删除
    created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 最后更新时间
    CONSTRAINT uk_skill_info_code UNIQUE (skill_code)
);


CREATE OR REPLACE TRIGGER trg_skill_info_updated_at BEFORE UPDATE ON skill_info FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =============================================================================
-- skill_version — 技能版本历史表
-- =============================================================================

CREATE TABLE IF NOT EXISTS skill_version (
    id          BIGSERIAL       PRIMARY KEY,                    -- 自增主键
    skill_code  VARCHAR(64)     NOT NULL,                 -- 关联技能编码
    version     INT             NOT NULL,                 -- 版本号
    git_commit  VARCHAR(64)     NOT NULL,                 -- 版本提交 hash
    git_path    VARCHAR(255)    DEFAULT NULL,             -- 仓库路径
    user_id     BIGINT          NOT NULL,                 -- 发布用户 ID
    introduce   VARCHAR(255)    DEFAULT NULL,             -- 版本变更说明
    deleted     SMALLINT        NOT NULL DEFAULT 0,       -- 软删除：0=正常 1=已删除
    created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    CONSTRAINT uk_skill_version UNIQUE (skill_code, version)
);


CREATE INDEX IF NOT EXISTS idx_skill_version_skill_code ON skill_version (skill_code);