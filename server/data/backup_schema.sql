-- AutoAudit Database Schema Backup
-- Generated: 2025-10-28
-- Total tables: 31

-- SEED DATA IDENTIFIED:
-- - states: 1 row (Oklahoma)
-- - llm_model_config: 5 rows (operation type mappings)
-- - page_types: 18 rows (VDP, Homepage, etc.)
-- - preamble_templates: 1 row (Standard Hierarchical)

CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

CREATE TABLE compliance_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                state_code TEXT NOT NULL,
                template_id TEXT,
                overall_score INTEGER,
                compliance_status TEXT,
                summary TEXT,
                llm_input_path TEXT,
                report_path TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, text_analysis_tokens INTEGER DEFAULT 0, visual_tokens INTEGER DEFAULT 0, total_tokens INTEGER DEFAULT 0, llm_input_text TEXT,
                FOREIGN KEY (url_id) REFERENCES urls(id),
                FOREIGN KEY (template_id) REFERENCES templates(template_id)
            );

CREATE TABLE default_page_type_preambles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_type_code TEXT NOT NULL,
            preamble_id INTEGER NOT NULL,
            active_version_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_type_code) REFERENCES page_types(code),
            FOREIGN KEY (preamble_id) REFERENCES preambles(id),
            FOREIGN KEY (active_version_id) REFERENCES preamble_versions(id),
            UNIQUE(page_type_code)
        );

CREATE TABLE extraction_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT NOT NULL UNIQUE,
                platform TEXT NOT NULL,
                selectors JSON NOT NULL,
                cleanup_rules JSON,
                extraction_order JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE "legislation_digests" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legislation_source_id INTEGER NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            active BOOLEAN DEFAULT 1,
            interpreted_requirements TEXT NOT NULL,
            approved BOOLEAN DEFAULT 0,
            created_by INTEGER,
            reviewed_by INTEGER,
            last_review_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        );

CREATE TABLE legislation_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_code TEXT NOT NULL,
            statute_number TEXT NOT NULL,
            title TEXT NOT NULL,
            full_text TEXT NOT NULL,
            source_url TEXT,
            effective_date DATE,
            sunset_date DATE,
            last_verified_date DATE,
            applies_to_page_types TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (state_code) REFERENCES states(code),
            UNIQUE(state_code, statute_number)
        );

CREATE TABLE llm_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_id INTEGER NOT NULL,
            call_type TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (check_id) REFERENCES compliance_checks (id) ON DELETE CASCADE
        );

CREATE TABLE llm_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Request Context
            api_endpoint TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            user_id INTEGER,

            -- LLM Details
            model TEXT NOT NULL,
            provider TEXT DEFAULT 'openai',

            -- Input/Output
            input_text TEXT NOT NULL,
            output_text TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            total_tokens INTEGER NOT NULL,

            -- Cost Tracking (USD)
            input_cost_usd REAL,
            output_cost_usd REAL,
            total_cost_usd REAL,

            -- Performance
            duration_ms INTEGER,

            -- Status
            status TEXT NOT NULL DEFAULT 'success' CHECK(
                status IN ('success', 'error', 'timeout')
            ),
            error_message TEXT,

            -- Metadata
            request_id TEXT,
            related_entity_type TEXT,
            related_entity_id INTEGER,

            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE llm_model_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL UNIQUE,
            model TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE page_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
, preamble TEXT, extraction_template TEXT, requires_llm_visual_confirmation BOOLEAN DEFAULT 0, requires_human_confirmation BOOLEAN DEFAULT 0);

CREATE TABLE preamble_composition_deps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composition_id INTEGER NOT NULL,
            depends_on_version_id INTEGER NOT NULL,
            FOREIGN KEY (composition_id) REFERENCES preamble_compositions(id) ON DELETE CASCADE,
            FOREIGN KEY (depends_on_version_id) REFERENCES preamble_versions(id) ON DELETE CASCADE,
            UNIQUE(composition_id, depends_on_version_id)
        );

CREATE TABLE preamble_compositions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composition_hash TEXT NOT NULL UNIQUE,
            template_id INTEGER NOT NULL,
            universal_version_id INTEGER,
            state_version_id INTEGER,
            page_type_version_id INTEGER,
            project_version_id INTEGER,
            composed_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hit_count INTEGER DEFAULT 0,
            FOREIGN KEY (template_id) REFERENCES preamble_templates(id),
            FOREIGN KEY (universal_version_id) REFERENCES preamble_versions(id),
            FOREIGN KEY (state_version_id) REFERENCES preamble_versions(id),
            FOREIGN KEY (page_type_version_id) REFERENCES preamble_versions(id),
            FOREIGN KEY (project_version_id) REFERENCES preamble_versions(id)
        );

CREATE TABLE preamble_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            template_structure TEXT NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE preamble_test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preamble_version_id INTEGER NOT NULL,
            url_id INTEGER NOT NULL,
            run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score_achieved REAL,
            violations_found TEXT,
            confidence_score REAL,
            token_count INTEGER,
            cost REAL,
            duration_seconds REAL,
            model_used TEXT,
            false_positive BOOLEAN,
            false_negative BOOLEAN,
            FOREIGN KEY (preamble_version_id) REFERENCES preamble_versions(id),
            FOREIGN KEY (url_id) REFERENCES urls(id)
        );

CREATE TABLE preamble_version_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preamble_version_id INTEGER NOT NULL,
            test_runs_count INTEGER DEFAULT 0,
            avg_score REAL,
            score_stddev REAL,
            avg_confidence REAL,
            false_positive_rate REAL,
            false_negative_rate REAL,
            avg_cost REAL,
            avg_duration_seconds REAL,
            last_tested_at TIMESTAMP,
            FOREIGN KEY (preamble_version_id) REFERENCES preamble_versions(id),
            UNIQUE(preamble_version_id)
        );

CREATE TABLE preamble_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preamble_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            preamble_text TEXT NOT NULL,
            change_summary TEXT,
            status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'active', 'retired')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (preamble_id) REFERENCES preambles(id),
            UNIQUE(preamble_id, version_number)
        );

CREATE TABLE preambles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            machine_name TEXT NOT NULL UNIQUE,
            scope TEXT NOT NULL CHECK(scope IN ('universal', 'state', 'page_type', 'project')),
            page_type_code TEXT,
            state_code TEXT,
            project_id INTEGER,
            created_via TEXT NOT NULL CHECK(created_via IN ('config', 'project_override')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (page_type_code) REFERENCES page_types(code),
            FOREIGN KEY (state_code) REFERENCES states(code),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );

CREATE TABLE project_page_type_preambles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            page_type_code TEXT NOT NULL,
            preamble_id INTEGER NOT NULL,
            active_version_id INTEGER NOT NULL,
            override_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (page_type_code) REFERENCES page_types(code),
            FOREIGN KEY (preamble_id) REFERENCES preambles(id),
            FOREIGN KEY (active_version_id) REFERENCES preamble_versions(id),
            UNIQUE(project_id, page_type_code)
        );

CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                state_code TEXT NOT NULL,
                base_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            , screenshot_path TEXT, deleted_at TIMESTAMP);

CREATE TABLE refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                device_info TEXT,
                ip_address TEXT,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                revoked_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

CREATE TABLE rule_collisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER NOT NULL,
            collides_with_rule_id INTEGER NOT NULL,
            collision_type TEXT NOT NULL CHECK(
                collision_type IN ('duplicate', 'semantic', 'conflict', 'overlap', 'supersedes')
            ),
            confidence REAL,
            ai_explanation TEXT,
            resolution TEXT CHECK(
                resolution IS NULL OR
                resolution IN ('keep_both', 'keep_existing', 'keep_new', 'merge', 'pending')
            ),
            resolved_by INTEGER,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (rule_id)
                REFERENCES rules(id) ON DELETE CASCADE,
            FOREIGN KEY (collides_with_rule_id)
                REFERENCES rules(id) ON DELETE CASCADE
        );

CREATE TABLE rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_code TEXT NOT NULL,
        legislation_source_id INTEGER,
        rule_text TEXT NOT NULL,
        applies_to_page_types TEXT,
        active BOOLEAN DEFAULT 1,
        approved BOOLEAN DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL, legislation_digest_id INTEGER, is_manually_modified BOOLEAN DEFAULT 0, original_rule_text TEXT, status TEXT DEFAULT "active", supersedes_rule_id INTEGER,
        FOREIGN KEY (legislation_source_id) REFERENCES legislation_sources(id) ON DELETE CASCADE
    );

CREATE TABLE schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE template_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT NOT NULL,
                rule_key TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence REAL NOT NULL,
                verification_method TEXT,
                notes TEXT,
                verified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES templates(template_id),
                UNIQUE(template_id, rule_key)
            );

CREATE TABLE templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT NOT NULL UNIQUE,
                platform TEXT NOT NULL,
                template_type TEXT DEFAULT 'compliance',
                config JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                url TEXT NOT NULL UNIQUE,
                url_type TEXT DEFAULT 'vdp',
                template_id TEXT,
                platform TEXT,
                active BOOLEAN DEFAULT 1,
                check_frequency_hours INTEGER DEFAULT 24,
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (template_id) REFERENCES templates(template_id)
            );

CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

CREATE TABLE violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                rule_violated TEXT NOT NULL,
                rule_key TEXT,
                confidence REAL,
                needs_visual_verification BOOLEAN DEFAULT 0,
                explanation TEXT,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (check_id) REFERENCES compliance_checks(id)
            );

CREATE TABLE visual_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_id INTEGER NOT NULL,
                violation_id INTEGER,
                rule_key TEXT NOT NULL,
                rule_text TEXT,
                is_compliant BOOLEAN NOT NULL,
                confidence REAL NOT NULL,
                verification_method TEXT DEFAULT 'visual',
                visual_evidence TEXT,
                proximity_description TEXT,
                screenshot_path TEXT,
                cached BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tokens_used INTEGER DEFAULT 0,
                FOREIGN KEY (check_id) REFERENCES compliance_checks(id),
                FOREIGN KEY (violation_id) REFERENCES violations(id)
            );

CREATE INDEX idx_collisions_by_existing
        ON rule_collisions(collides_with_rule_id)
    ;

CREATE INDEX idx_collisions_by_rule
        ON rule_collisions(rule_id)
    ;

CREATE INDEX idx_collisions_pending
        ON rule_collisions(resolution)
        WHERE resolution IS NULL OR resolution = 'pending'
    ;

CREATE INDEX idx_digests_by_source
        ON legislation_digests(legislation_source_id)
    ;

CREATE INDEX idx_legislation_sources_state ON legislation_sources(state_code);

CREATE INDEX idx_llm_calls_check_id ON llm_calls(check_id)
    ;

CREATE INDEX idx_llm_logs_cost
        ON llm_logs(total_cost_usd)
    ;

CREATE INDEX idx_llm_logs_created
        ON llm_logs(created_at)
    ;

CREATE INDEX idx_llm_logs_endpoint
        ON llm_logs(api_endpoint)
    ;

CREATE INDEX idx_llm_logs_model
        ON llm_logs(model)
    ;

CREATE INDEX idx_llm_logs_operation
        ON llm_logs(operation_type)
    ;

CREATE INDEX idx_llm_logs_status
        ON llm_logs(status)
    ;

CREATE INDEX idx_llm_logs_user
        ON llm_logs(user_id)
    ;

CREATE UNIQUE INDEX idx_one_active_digest_per_source
        ON legislation_digests(legislation_source_id, active)
        WHERE active = 1
    ;

CREATE INDEX idx_preamble_compositions_hash ON preamble_compositions(composition_hash);

CREATE INDEX idx_preamble_test_runs_version ON preamble_test_runs(preamble_version_id);

CREATE INDEX idx_preamble_versions_preamble ON preamble_versions(preamble_id);

CREATE INDEX idx_preamble_versions_status ON preamble_versions(status);

CREATE INDEX idx_rules_active ON rules(active);

CREATE INDEX idx_rules_approved ON rules(approved);

CREATE INDEX idx_rules_by_digest
            ON rules(legislation_digest_id)
        ;

CREATE INDEX idx_rules_legislation_source ON rules(legislation_source_id);

CREATE INDEX idx_rules_state_code ON rules(state_code);

CREATE INDEX idx_rules_status
            ON rules(status)
        ;

