CREATE TABLE IF NOT EXISTS patients (
  id INTEGER PRIMARY KEY,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  birth_date DATE NOT NULL,
  gender VARCHAR(20),
  phone VARCHAR(50),
  email VARCHAR(255),
  created_at TIMESTAMPTZ NULL,
  updated_at TIMESTAMPTZ NULL
);
