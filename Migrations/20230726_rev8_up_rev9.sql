CREATE TABLE IF NOT EXISTS user_inv (
    id SERIAL PRIMARY KEY,
    owner_id BIGINT,
    guild_id BIGINT,
    amount_owned INT DEFAULT 0,
    item_id INT FOREIGN KEY REFERENCES eco_item (id) ON DELETE CASCADE ON UPDATE NO ACTION
);

CREATE INDEX IF NOT EXISTS user_inv_owner_idx ON user_inv (owner_id);
CREATE INDEX IF NOT EXISTS user_inv_guild_idx ON user_inv (guild_id);
CREATE INDEX IF NOT EXISTS user_inv_item_idx ON user_inv (item_id);