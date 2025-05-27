-- Create test database
CREATE DATABASE IF NOT EXISTS razorpay_emandate_test;

-- Grant permissions
GRANT ALL PRIVILEGES ON razorpay_emandate.* TO 'razorpay_user'@'%';
GRANT ALL PRIVILEGES ON razorpay_emandate_test.* TO 'razorpay_user'@'%';
FLUSH PRIVILEGES;
