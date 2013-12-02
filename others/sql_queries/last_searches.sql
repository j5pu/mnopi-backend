SELECT users.username, searches.search_query, searches.date
FROM searches INNER JOIN users ON (searches.user_id = users.id)
ORDER by searches.date DESC
LIMIT 10