package 'httpd' do
    action :install
end

file '/var/www/html/index.html' do
  content '<h1>Hellow World</h1>'
end

service 'httpd' do
  action [:start, :enable]
end   

#sudo chef-client local-mode server.rb   - to run the recipe

