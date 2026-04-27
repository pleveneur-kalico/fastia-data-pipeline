-- Schéma de la base de données FastIA
-- Compatible MySQL 8.0+

CREATE DATABASE IF NOT EXISTS fastia_db;
USE fastia_db;

DROP TABLE IF EXISTS demandes;

CREATE TABLE demandes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    input_text      TEXT NOT NULL,
    input_raw       TEXT,
    categorie       VARCHAR(50) NOT NULL,
    priorite        VARCHAR(20) NOT NULL,
    reponse_suggeree TEXT,
    source          VARCHAR(30) NOT NULL,      -- 'original' | 'synthetic'
    canal           VARCHAR(30) DEFAULT 'web', -- 'email' | 'web' | 'chat'
    langue          VARCHAR(10) DEFAULT 'fr',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dataset_version VARCHAR(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_demandes_categorie ON demandes(categorie);
CREATE INDEX idx_demandes_source ON demandes(source);
CREATE INDEX idx_demandes_version ON demandes(dataset_version);
