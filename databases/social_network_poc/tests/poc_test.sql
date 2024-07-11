-- Query 1: Retrieve all users with their email addresses
SELECT username, email FROM Users;

-- Query 2: List all tweets with their authors
SELECT t.content, u.username
FROM Tweets t
JOIN Users u ON t.user_id = u.user_id;

-- Query 3: Find who user 'alice' is following
SELECT u2.username
FROM Users u1
JOIN Follows f ON u1.user_id = f.follower_id
JOIN Users u2 ON f.followee_id = u2.user_id
WHERE u1.username = 'alice';

-- Query 4: Count the number of followers for each user
SELECT u.username, COUNT(f.follower_id) AS followers_count
FROM Users u
LEFT JOIN Follows f ON u.user_id = f.followee_id
GROUP BY u.user_id;

-- Query 5: Retrieve all tweets and their respective like counts
SELECT t.content, COUNT(l.like_id) AS like_count
FROM Tweets t
LEFT JOIN Likes l ON t.tweet_id = l.tweet_id
GROUP BY t.tweet_id;

-- Query 6: Find all comments for a specific tweet
SELECT c.content, u.username
FROM Comments c
JOIN Users u ON c.user_id = u.user_id
WHERE c.tweet_id = 1;

-- Query 7: List users who liked tweets posted by 'alice'
SELECT DISTINCT u.username
FROM Likes l
JOIN Tweets t ON l.tweet_id = t.tweet_id
JOIN Users u ON l.user_id = u.user_id
WHERE t.user_id = (SELECT user_id FROM Users WHERE username = 'alice');

-- Query 8: Find the tweet with the most comments
SELECT t.content, COUNT(c.comment_id) AS comments_count
FROM Tweets t
LEFT JOIN Comments c ON t.tweet_id = c.tweet_id
GROUP BY t.tweet_id
ORDER BY comments_count DESC
LIMIT 1;

-- Query 9: Retrieve users who have never posted a tweet
SELECT u.username
FROM Users u
LEFT JOIN Tweets t ON u.user_id = t.user_id
WHERE t.tweet_id IS NULL;

-- Query 10: List tweets liked by users who follow 'alice'
SELECT DISTINCT t.content
FROM Tweets t
JOIN Likes l ON t.tweet_id = l.tweet_id
JOIN Follows f ON l.user_id = f.follower_id
WHERE f.followee_id = (SELECT user_id FROM Users WHERE username = 'alice');
