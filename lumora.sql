-- Lumora PostgreSQL schema generated from SQLModel metadata.
-- This is schema only; it contains no user or chat data.


CREATE TABLE users (
	id SERIAL NOT NULL,
	name VARCHAR(100) NOT NULL,
	email VARCHAR(150) NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	role VARCHAR(10) NOT NULL,
	birth_date DATE,
	avatar_url VARCHAR(300),
	is_active BOOLEAN NOT NULL,
	failed_logins INTEGER NOT NULL,
	locked_until TIMESTAMP WITHOUT TIME ZONE,
	totp_secret VARCHAR(64),
	totp_enabled BOOLEAN NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (id)
)

;

CREATE UNIQUE INDEX ix_users_email ON users (email);


CREATE TABLE services (
	id SERIAL NOT NULL,
	code VARCHAR(20) NOT NULL,
	name VARCHAR(100) NOT NULL,
	price INTEGER NOT NULL,
	is_active BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (code)
)

;


CREATE TABLE tarot_cards (
	id SERIAL NOT NULL,
	name VARCHAR(100) NOT NULL,
	suit VARCHAR(30) NOT NULL,
	upright VARCHAR(300) NOT NULL,
	reversed_meaning VARCHAR(300) NOT NULL,
	image_url VARCHAR(300),
	PRIMARY KEY (id),
	UNIQUE (name)
)

;


CREATE TABLE arcana (
	id SERIAL NOT NULL,
	number INTEGER NOT NULL,
	name VARCHAR(60) NOT NULL,
	keywords VARCHAR(200) NOT NULL,
	personality TEXT DEFAULT '' NOT NULL,
	talent TEXT DEFAULT '' NOT NULL,
	life_purpose TEXT DEFAULT '' NOT NULL,
	relationship TEXT DEFAULT '' NOT NULL,
	career_money TEXT DEFAULT '' NOT NULL,
	karmic_lesson TEXT DEFAULT '' NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (number)
)

;


CREATE TABLE zodiac_signs (
	id SERIAL NOT NULL,
	name VARCHAR(30) NOT NULL,
	start_month INTEGER NOT NULL,
	start_day INTEGER NOT NULL,
	end_month INTEGER NOT NULL,
	end_day INTEGER NOT NULL,
	element VARCHAR(20) NOT NULL,
	traits VARCHAR(500) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name)
)

;


CREATE TABLE shio_animals (
	id SERIAL NOT NULL,
	cycle_index INTEGER NOT NULL,
	name VARCHAR(30) NOT NULL,
	traits VARCHAR(500) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (cycle_index),
	UNIQUE (name)
)

;


CREATE TABLE imlek_dates (
	year SERIAL NOT NULL,
	new_year_date DATE NOT NULL,
	PRIMARY KEY (year)
)

;


CREATE TABLE chat_keywords (
	id SERIAL NOT NULL,
	category VARCHAR(30) NOT NULL,
	keywords VARCHAR(500) NOT NULL,
	source VARCHAR(100) NOT NULL,
	weight INTEGER NOT NULL,
	is_active BOOLEAN NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE webhook_events (
	id SERIAL NOT NULL,
	event_id VARCHAR(100) NOT NULL,
	order_code VARCHAR(20),
	status VARCHAR(20) NOT NULL,
	received_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (event_id)
)

;


CREATE TABLE user_avatars (
	user_id INTEGER NOT NULL,
	content_type VARCHAR(20) NOT NULL,
	data BYTEA NOT NULL,
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE login_sessions (
	id SERIAL NOT NULL,
	user_id INTEGER NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	user_agent VARCHAR(200) NOT NULL,
	ip VARCHAR(45),
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	last_seen_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	revoked BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	UNIQUE (token_hash)
)

;

CREATE INDEX ix_login_sessions_user_id ON login_sessions (user_id);


CREATE TABLE audit_logs (
	id SERIAL NOT NULL,
	user_id INTEGER,
	event VARCHAR(40) NOT NULL,
	detail VARCHAR(300) NOT NULL,
	ip VARCHAR(45),
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE orders (
	id SERIAL NOT NULL,
	order_code VARCHAR(20),
	user_id INTEGER NOT NULL,
	service_id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	status VARCHAR(12) NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	expires_at TIMESTAMP WITHOUT TIME ZONE,
	paid_at TIMESTAMP WITHOUT TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	FOREIGN KEY(service_id) REFERENCES services (id)
)

;

CREATE INDEX ix_orders_user_id ON orders (user_id);

CREATE UNIQUE INDEX ix_orders_order_code ON orders (order_code);


CREATE TABLE payments (
	id SERIAL NOT NULL,
	order_id INTEGER NOT NULL,
	gateway VARCHAR(20) NOT NULL,
	gateway_ref VARCHAR(100),
	method VARCHAR(20) NOT NULL,
	amount INTEGER NOT NULL,
	status VARCHAR(12) NOT NULL,
	signature_valid BOOLEAN NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	settled_at TIMESTAMP WITHOUT TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(order_id) REFERENCES orders (id),
	UNIQUE (gateway_ref)
)

;

CREATE INDEX ix_payments_order_id ON payments (order_id);


CREATE TABLE readings (
	id SERIAL NOT NULL,
	user_id INTEGER NOT NULL,
	type VARCHAR(20) NOT NULL,
	title VARCHAR(150) NOT NULL,
	order_id INTEGER,
	result_json TEXT DEFAULT '' NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	FOREIGN KEY(order_id) REFERENCES orders (id)
)

;

CREATE INDEX ix_readings_user_id ON readings (user_id);


CREATE TABLE tarot_draws (
	id SERIAL NOT NULL,
	reading_id INTEGER NOT NULL,
	card_id INTEGER NOT NULL,
	position INTEGER NOT NULL,
	position_label VARCHAR(30) NOT NULL,
	is_reversed BOOLEAN NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (reading_id, position),
	FOREIGN KEY(reading_id) REFERENCES readings (id),
	FOREIGN KEY(card_id) REFERENCES tarot_cards (id)
)

;

CREATE INDEX ix_tarot_draws_reading_id ON tarot_draws (reading_id);


CREATE TABLE matrix_readings (
	id SERIAL NOT NULL,
	reading_id INTEGER NOT NULL,
	birth_date DATE NOT NULL,
	day_num INTEGER NOT NULL,
	month_num INTEGER NOT NULL,
	year_num INTEGER NOT NULL,
	sum_num INTEGER NOT NULL,
	center_num INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (reading_id),
	FOREIGN KEY(reading_id) REFERENCES readings (id)
)

;


CREATE TABLE zodiac_readings (
	id SERIAL NOT NULL,
	reading_id INTEGER NOT NULL,
	birth_date DATE NOT NULL,
	zodiac_id INTEGER NOT NULL,
	shio_id INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (reading_id),
	FOREIGN KEY(reading_id) REFERENCES readings (id),
	FOREIGN KEY(zodiac_id) REFERENCES zodiac_signs (id),
	FOREIGN KEY(shio_id) REFERENCES shio_animals (id)
)

;


CREATE TABLE chat_sessions (
	id SERIAL NOT NULL,
	reading_id INTEGER NOT NULL,
	source VARCHAR(20) NOT NULL,
	relationship_status VARCHAR(20),
	my_gender VARCHAR(10),
	other_gender VARCHAR(10),
	my_alias VARCHAR(50) NOT NULL,
	other_alias VARCHAR(50) NOT NULL,
	consent_given BOOLEAN NOT NULL,
	intent_enabled BOOLEAN NOT NULL,
	total_messages INTEGER NOT NULL,
	first_message_at TIMESTAMP WITHOUT TIME ZONE,
	last_message_at TIMESTAMP WITHOUT TIME ZONE,
	status VARCHAR(12) NOT NULL,
	error_message VARCHAR(200),
	interest_trend VARCHAR(10),
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (reading_id),
	FOREIGN KEY(reading_id) REFERENCES readings (id)
)

;


CREATE TABLE closeness_predictions (
	id SERIAL NOT NULL,
	reading_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	my_alias VARCHAR(50) NOT NULL,
	other_alias VARCHAR(50) NOT NULL,
	total_messages INTEGER NOT NULL,
	frequency FLOAT NOT NULL,
	consistency FLOAT NOT NULL,
	balance FLOAT NOT NULL,
	reply FLOAT NOT NULL,
	initiative FLOAT NOT NULL,
	warmth FLOAT NOT NULL,
	rule_score INTEGER NOT NULL,
	rule_level VARCHAR(20) NOT NULL,
	ml_level VARCHAR(20),
	ml_confidence FLOAT,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(reading_id) REFERENCES readings (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE INDEX ix_closeness_predictions_user_id ON closeness_predictions (user_id);

CREATE UNIQUE INDEX ix_closeness_predictions_reading_id ON closeness_predictions (reading_id);


CREATE TABLE chat_person_stats (
	id SERIAL NOT NULL,
	chat_session_id INTEGER NOT NULL,
	person VARCHAR(5) NOT NULL,
	bubbles INTEGER NOT NULL,
	avg_length FLOAT NOT NULL,
	reply_rate FLOAT NOT NULL,
	first_message_pct FLOAT NOT NULL,
	median_response_sec INTEGER,
	double_texts INTEGER NOT NULL,
	question_count INTEGER NOT NULL,
	deleted_count INTEGER NOT NULL,
	excited_score INTEGER NOT NULL,
	excited_factors VARCHAR(500) NOT NULL,
	hourly_json VARCHAR(600) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (chat_session_id, person),
	FOREIGN KEY(chat_session_id) REFERENCES chat_sessions (id)
)

;

CREATE INDEX ix_chat_person_stats_chat_session_id ON chat_person_stats (chat_session_id);


CREATE TABLE chat_indicator_scores (
	id SERIAL NOT NULL,
	chat_session_id INTEGER NOT NULL,
	person VARCHAR(5) NOT NULL,
	category VARCHAR(30) NOT NULL,
	hit_count INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(chat_session_id) REFERENCES chat_sessions (id)
)

;

CREATE INDEX ix_chat_indicator_scores_chat_session_id ON chat_indicator_scores (chat_session_id);


CREATE TABLE chat_signals (
	id SERIAL NOT NULL,
	chat_session_id INTEGER NOT NULL,
	signal VARCHAR(100) NOT NULL,
	quote VARCHAR(300) NOT NULL,
	confidence VARCHAR(10) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(chat_session_id) REFERENCES chat_sessions (id)
)

;

CREATE INDEX ix_chat_signals_chat_session_id ON chat_signals (chat_session_id);
