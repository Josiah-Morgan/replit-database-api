# replit-database-api
A custom API for a discord bot I had. I don't think this will work anymore. Made sometime in early 2023

# Ways to use the database
/db/FranchiseRoles - deletes the whole table
/db/FranchiseRoles/guild_id - deletes a whole key
/db/FranchiseRoles/guild_id/role_id - deletes something in a list or dict
/db/FranchiseRoles/guild_id/role_id/role_name - deletes a nested value (can go through multiple list, dicts, etc. to get the specific value you want)

## Where I used it
[Bread Winner B](https://github.com/Josiah-Morgan/Bread-Winner-B-Code)
[Database file on the bot](https://github.com/Josiah-Morgan/Bread-Winner-B/blob/current/utils/database.py)
