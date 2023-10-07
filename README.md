Minicloak Microservice

This microservice provides user authentication and user management functionality.
It utilizes Flask as the web framework, SQLAlchemy for database management, and JWT for authentication.

WARNING: This microservice is NOT intended for production use. It is meant to be used as a learning/development tool.

static files: static/{css,js}
templates: templates/

It includes the following endpoints for user authentication:
- POST /auth/authenticate: Authenticate a user and return a JWT token.
- POST /auth/verify: Verify the validity of a JWT token.
- POST /auth/refresh: Refresh a JWT token using a refresh token.
- POST /auth/logout: Logout a user by deleting the refresh token.

It also includes the following endpoints for user management:
- GET    /api/users: Get a list of all users.
- POST   /api/users: Create a new user.
- POST   /api/users/<id>: Edit a specific user.
- DELETE /api/users/<id>: Delete a specific user.

It also includes the following endpoints for the user management interface:
- /users: Render a page of a list of all users.
- /users/create: Render a page for creating a new user.
- /users/<id>/edit: Render a page for editing a specific user.

It includes the following sample users:
- admin: role=admin, clearance=gold
- gold: role=user, clearance=gold, team=frontend, team=backend, team=devops
- silver: role=user, clearance=silver, team=frontend
- bronze: role=user, clearance=bronze, team=devops
- guest: No attributes

SQLite is used as the database backend.