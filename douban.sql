CREATE TABLE IF NOT EXISTS douban_top100 (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    director VARCHAR(50),
    year INT,
    rating DECIMAL(3,1),
    quote VARCHAR(255)
);

--
-- id（主键）
-- title（电影名）
-- director（导演）
-- year（年份）
-- rating（评分）
-- quote（短评）
--
