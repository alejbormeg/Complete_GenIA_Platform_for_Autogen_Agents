CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(100) NOT NULL,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Tweets (
    tweet_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Follows (
    follower_id INTEGER NOT NULL,
    followee_id INTEGER NOT NULL,
    followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followee_id),
    FOREIGN KEY (follower_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (followee_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Likes (
    like_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tweet_id INTEGER NOT NULL,
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (tweet_id) REFERENCES Tweets(tweet_id) ON DELETE CASCADE
);

CREATE TABLE Comments (
    comment_id SERIAL PRIMARY KEY,
    tweet_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tweet_id) REFERENCES Tweets(tweet_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);


-- Insert Users
INSERT INTO Users (username, email, password_hash, bio) VALUES
('alice', 'alice@example.com', 'hash1', 'Bio for Alice'),
('bob', 'bob@example.com', 'hash2', 'Bio for Bob'),
('charlie', 'charlie@example.com', 'hash3', 'Bio for Charlie'),
('cris', 'cris@example.com', 'hash4', 'Bio for Cris'),
('dave', 'dave@example.com', 'hash4', 'Bio for Dave'),
('eve', 'eve@example.com', 'hash5', 'Bio for Eve');

-- Insert Tweets
INSERT INTO Tweets (user_id, content) VALUES
(1, 'Hello, this is Alice!'), -- tweet_id 1
(2, 'Hi, Bob here.'), -- tweet_id 2
(1, 'Another tweet from Alice.'), -- tweet_id 3
(3, 'Charlie checking in!'), -- tweet_id 4
(4, 'Dave says hello.'), -- tweet_id 5
(5, 'Eve here, nice to meet you!'); -- tweet_id 6

-- Insert Follows (Alice has followers)
INSERT INTO Follows (follower_id, followee_id) VALUES
(2, 1), -- Bob follows Alice
(3, 1), -- Charlie follows Alice
(4, 1), -- Dave follows Alice
(5, 1); -- Eve follows Alice

-- Insert Likes (Followers of Alice liking tweets)
INSERT INTO Likes (user_id, tweet_id) VALUES
(2, 1), -- Bob likes Alice's tweet
(3, 1), -- Charlie likes Alice's tweet
(4, 3), -- Dave likes Alice's another tweet
(5, 3), -- Eve likes Alice's another tweet
(2, 4), -- Bob likes Charlie's tweet
(3, 2), -- Charlie likes Bob's tweet
(4, 5), -- Dave likes his own tweet
(5, 6); -- Eve likes her own tweet

-- Insert Comments
INSERT INTO Comments (tweet_id, user_id, content) VALUES
(1, 2, 'Nice to see you here, Alice!'),
(1, 3, 'Hello Alice!'),
(2, 1, 'Hi Bob!'),
(4, 1, 'Welcome Charlie!');
