SELECT DISTINCT domains.domain, user_category.name AS category
FROM pages_visited INNER JOIN domains ON (pages_visited.domain_id = domains.id)
INNER JOIN domains_categories ON (domains.id = domains_categories.categorizeddomain_id)
INNER JOIN user_category ON (domains_categories.usercategory_id = user_category.id)
ORDER BY domains.domain ASC