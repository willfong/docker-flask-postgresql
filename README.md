# Boilerplate: Docker / Flask / Postgresql

### Docker Stuff

```
docker build -t testimg .
docker run -d --rm -p 5000:80 --name=testapp -v $PWD:/app testimg
docker exec -it db psql -d mydb -U dbuser -f /app/schema.sql
```
