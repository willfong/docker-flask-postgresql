# Boilerplate: Docker / Flask / Postgresql

### Docker Stuff

```
docker container stop $(docker container ls -aq); docker container rm $(docker container ls -aq); docker image prune -a -f 
docker build -t testimg .
docker run -d --rm -p 5000:80 --name=testapp -v $PWD:/app testimg
docker exec -it db psql -d mydb -U dbuser -f /app/schema.sql
```

### Facebook Stuff

https://developers.facebook.com/

Settings -> Basic -> Add Platform

Website -> Callback URL: http://localhost:8080/auth/facebook/callback


https://developers.facebook.com/blog/post/2018/06/08/enforce-https-facebook-login/

You will still be able to use HTTP with “localhost” addresses, but only while your app is still in development mode.
