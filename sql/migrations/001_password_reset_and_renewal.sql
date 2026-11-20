CREATE TABLE IF NOT EXISTS password_reset_codes (
    userID INT NOT NULL PRIMARY KEY,
    code_hash VARCHAR(60) NOT NULL,
    expires_at DATETIME NOT NULL,
    requested_at DATETIME NOT NULL,
    attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT fk_reset_user FOREIGN KEY (userID) REFERENCES users(userID) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS renewal_requests (
    borrowingID INT NOT NULL PRIMARY KEY,
    requested_due_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_renewal_request_status CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    CONSTRAINT fk_renewal_loan FOREIGN KEY (borrowingID) REFERENCES borrowing_records(borrowingID) ON DELETE CASCADE
) ENGINE=InnoDB;
