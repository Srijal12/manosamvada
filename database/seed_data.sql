USE manosamvada_db;

-- ── Crisis Keywords ───────────────────────────────────────────────────────────
INSERT INTO crisis_keywords (keyword, category, severity) VALUES
('suicide', 'self-harm', 3),
('suicidal', 'self-harm', 3),
('kill myself', 'self-harm', 3),
('end my life', 'self-harm', 3),
('want to die', 'self-harm', 3),
('self harm', 'self-harm', 2),
('self-harm', 'self-harm', 2),
('cut myself', 'self-harm', 2),
('hurt myself', 'self-harm', 2),
('no reason to live', 'self-harm', 3),
('better off dead', 'self-harm', 3),
('cant go on', 'self-harm', 3),
('give up on life', 'self-harm', 3),
('overdose', 'self-harm', 2),
('not worth living', 'self-harm', 3),
('ending it all', 'self-harm', 3);

-- ── Response Templates ────────────────────────────────────────────────────────
INSERT INTO response_templates (emotion, template) VALUES
('happy', 'It''s wonderful to hear that! Your positive energy is infectious. What has been making you feel this way?'),
('sad', 'I hear you, and I want you to know that your feelings are completely valid. You''re not alone in this. Would you like to share more?'),
('angry', 'I can feel the intensity of what you''re going through. It makes complete sense to feel frustrated. Tell me more about what happened.'),
('anxious', 'Anxiety can feel so overwhelming. Let''s take this one breath at a time. I''m right here with you.'),
('neutral', 'Thank you for sharing that with me. I''m here to listen - what''s on your mind today?'),
('crisis', 'I hear you, and I''m deeply concerned about you right now. Your life has enormous value. Please reach out to a crisis helpline immediately.');

-- ── Default Admin User ─────────────────────────────────────────────────────────
-- IMPORTANT: this placeholder hash does NOT correspond to a real password.
-- Generate your own with: python -c "import bcrypt; print(bcrypt.hashpw(b'YourNewPassword1!', bcrypt.gensalt()).decode())"
-- and replace the value below before running this seed file.
INSERT INTO users (username, email, password_hash, is_verified, is_admin)
VALUES (
    'admin',
    'admin@manosamvada.com',
    '$2b$12$REPLACE.WITH.YOUR.OWN.BCRYPT.HASH.BEFORE.DEPLOYMENT........',
    1,
    1
);
