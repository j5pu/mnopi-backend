SELECT users.username, pages_visited.date, pages_visited.page_visited 
FROM pages_visited INNER JOIN users ON (pages_visited.user_id = users.id)
ORDER BY pages_visited.date DESC
LIMIT 10