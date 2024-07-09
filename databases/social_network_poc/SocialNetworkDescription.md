# PostgreSQL Database Schema Documentation

## Tables

### Users
This table stores user information.

- **user_id**: `SERIAL PRIMARY KEY`, a unique identifier for each user.
- **username**: `VARCHAR(50) NOT NULL UNIQUE`, the user's unique username.
- **email**: `VARCHAR(100) NOT NULL UNIQUE`, the user's unique email address.
- **password_hash**: `VARCHAR(100) NOT NULL`, a hashed representation of the user's password.
- **bio**: `TEXT`, a short biography or description of the user.
- **created_at**: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, the timestamp when the user was created.

### Tweets
This table stores tweets posted by users.

- **tweet_id**: `SERIAL PRIMARY KEY`, a unique identifier for each tweet.
- **user_id**: `INTEGER NOT NULL`, a reference to the user who posted the tweet.
- **content**: `TEXT NOT NULL`, the content of the tweet.
- **created_at**: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, the timestamp when the tweet was created.
- **FOREIGN KEY (user_id)**: `REFERENCES Users(user_id) ON DELETE CASCADE`, ensures that deleting a user also deletes their tweets.

### Follows
This table stores information about which users follow other users.

- **follower_id**: `INTEGER NOT NULL`, the user who is following another user.
- **followee_id**: `INTEGER NOT NULL`, the user who is being followed.
- **followed_at**: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, the timestamp when the follow action occurred.
- **PRIMARY KEY (follower_id, followee_id)**: ensures unique follower-followee pairs.
- **FOREIGN KEY (follower_id)**: `REFERENCES Users(user_id) ON DELETE CASCADE`, ensures that deleting a follower user deletes the follow relationship.
- **FOREIGN KEY (followee_id)**: `REFERENCES Users(user_id) ON DELETE CASCADE`, ensures that deleting a followee user deletes the follow relationship.

### Likes
This table stores information about which users like which tweets.

- **like_id**: `SERIAL PRIMARY KEY`, a unique identifier for each like.
- **user_id**: `INTEGER NOT NULL`, a reference to the user who liked the tweet.
- **tweet_id**: `INTEGER NOT NULL`, a reference to the liked tweet.
- **liked_at**: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, the timestamp when the like occurred.
- **FOREIGN KEY (user_id)**: `REFERENCES Users(user_id) ON DELETE CASCADE`, ensures that deleting a user also deletes their likes.
- **FOREIGN KEY (tweet_id)**: `REFERENCES Tweets(tweet_id) ON DELETE CASCADE`, ensures that deleting a tweet also deletes its likes.

### Comments
This table stores comments on tweets.

- **comment_id**: `SERIAL PRIMARY KEY`, a unique identifier for each comment.
- **tweet_id**: `INTEGER NOT NULL`, a reference to the tweet being commented on.
- **user_id**: `INTEGER NOT NULL`, a reference to the user who made the comment.
- **content**: `TEXT NOT NULL`, the content of the comment.
- **created_at**: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, the timestamp when the comment was created.
- **FOREIGN KEY (tweet_id)**: `REFERENCES Tweets(tweet_id) ON DELETE CASCADE`, ensures that deleting a tweet also deletes its comments.
- **FOREIGN KEY (user_id)**: `REFERENCES Users(user_id) ON DELETE CASCADE`, ensures that deleting a user also deletes their comments.