-- ============================================================
-- Manosamvada Database Schema
-- Normalized to 3NF
-- Engine: MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS manosamvada_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE manosamvada_db;

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    username        VARCHAR(50)     NOT NULL,
    email           VARCHAR(254)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    is_verified     TINYINT(1)      NOT NULL DEFAULT 0,
    is_admin        TINYINT(1)      NOT NULL DEFAULT 0,
    last_login      DATETIME        NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email    (email),
    UNIQUE KEY uq_users_username (username),
    INDEX idx_users_email        (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── OTP Storage ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS otp_store (
    email       VARCHAR(254)    NOT NULL,
    otp_hash    VARCHAR(64)     NOT NULL,
    expires_at  DATETIME        NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── Chat Sessions ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED    NOT NULL,
    title       VARCHAR(255)    NOT NULL DEFAULT 'New Conversation',
    is_active   TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY fk_sessions_user (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_sessions_user_id   (user_id),
    INDEX idx_sessions_active    (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── Chat Messages ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_messages (
    id                  INT UNSIGNED        NOT NULL AUTO_INCREMENT,
    session_id          INT UNSIGNED        NOT NULL,
    role                ENUM('user', 'assistant') NOT NULL,
    content             TEXT                NOT NULL,
    emotion_label       VARCHAR(20)         NULL,
    emotion_intensity   DECIMAL(5, 3)       NULL,
    created_at          DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY fk_messages_session (session_id)
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_messages_session_id   (session_id),
    INDEX idx_messages_created_at   (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── Crisis Keywords ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crisis_keywords (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    keyword     VARCHAR(100)    NOT NULL,
    category    VARCHAR(50)     NOT NULL DEFAULT 'general',
    severity    TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '1=moderate, 2=high, 3=critical',
    is_active   TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_crisis_keyword (keyword),
    INDEX idx_crisis_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── Crisis Event Logs ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crisis_logs (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED    NULL,
    message_snippet VARCHAR(200)    NOT NULL,
    detected_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed        TINYINT(1)      NOT NULL DEFAULT 0,
    reviewed_by     INT UNSIGNED    NULL,

    PRIMARY KEY (id),
    FOREIGN KEY fk_crisis_logs_user (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,
    INDEX idx_crisis_logs_reviewed (reviewed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── Response Templates ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS response_templates (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    emotion     VARCHAR(20)     NOT NULL,
    template    TEXT            NOT NULL,
    is_active   TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_templates_emotion (emotion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
