# Heroku starter for Django + React

Starter package for creating a Heroku dyno with Django API backend and React front end

## Setup
1. Create postgres for local copy
    > docker run --name postgres -e POSTGRES_PASSWORD=[insert password here] -p 5432:5432 -d postgres
2. Assign environment variables:
   1. POSTGRES_PASSWORD = [password used above]
   2. DJANGO_SECRET_KEY