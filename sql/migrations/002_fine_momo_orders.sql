CREATE TABLE IF NOT EXISTS fine_momo_orders (
    fineID INT NOT NULL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    partner_code VARCHAR(50) NOT NULL,
    amount INT UNSIGNED NOT NULL,
    state VARCHAR(12) NOT NULL DEFAULT 'Pending',
    pay_url TEXT,
    transaction_id BIGINT UNSIGNED UNIQUE,
    CONSTRAINT chk_fine_momo_order_state CHECK (state IN ('Pending', 'Failed', 'Paid')),
    CONSTRAINT fk_fine_momo_order FOREIGN KEY (fineID) REFERENCES fines(fineID) ON DELETE CASCADE
) ENGINE=InnoDB;
