// 登录表单处理
document.getElementById('loginForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const loginType = document.getElementById('loginType').value;
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const messageDiv = document.getElementById('message');
    
    if (!username || !password) {
        showMessage('请填写用户名和密码', 'error');
        return;
    }
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password, login_type: loginType })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('登录成功，正在跳转...', 'success');
            setTimeout(() => {
                // 使用服务器返回的重定向URL
                const redirectUrl = data.redirect_to || (loginType === 'admin' ? '/admin' : '/dashboard');
                window.location.href = redirectUrl;
            }, 500);
        } else {
            showMessage(data.message || '登录失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Login error:', error);
    }
});

// 注册表单处理
document.getElementById('registerForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const messageDiv = document.getElementById('message');
    
    if (!username || !password) {
        showMessage('请填写用户名和密码', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('密码长度至少6位', 'error');
        return;
    }
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('注册成功，正在跳转到登录页面...', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            showMessage(data.message || '注册失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Register error:', error);
    }
});

// 显示消息
function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.className = `message ${type}`;
        
        if (type === 'success') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 3000);
        }
    }
}

