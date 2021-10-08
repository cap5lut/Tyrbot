CREATE TABLE IF NOT EXISTS scout_info (playfield_id INT NOT NULL, site_number INT NOT NULL, ql INT NOT NULL, x_coord INT NOT NULL, y_coord INT NOT NULL, org_name VARCHAR(255) NOT NULL, org_id INT NOT NULL, faction VARCHAR(10) NOT NULL, close_time INT NOT NULL, penalty_duration INT NOT NULL, penalty_until INT NOT NULL, created_at INT NOT NULL, updated_at INT NOT NULL);