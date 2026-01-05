// 管理员界面JavaScript

// 显示指定部分
function showSection(sectionId) {
    // 隐藏所有部分
    document.querySelectorAll('.admin-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // 移除所有导航项的active类
    document.querySelectorAll('.top-nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 显示选中的部分
    document.getElementById(sectionId + '-section').classList.add('active');
    
    // 激活对应的导航项
    const navItem = document.querySelector(`.top-nav-item[href="#${sectionId}"]`);
    if (navItem) {
        navItem.classList.add('active');
    }
    
    // 根据部分加载数据
    switch(sectionId) {
        case 'users':
            loadUsers();
            break;
        case 'history':
            loadHistory();
            break;
        case 'statistics':
            loadStatistics();
            break;
        case 'storage':
            loadStorage();
            break;
        case 'logs':
            loadLogs();
            break;
    }
}

// 加载用户列表
async function loadUsers() {
    showLoading();
    try {
        const response = await fetch('/api/admin/users');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.getElementById('usersTableBody');
            tbody.innerHTML = '';
            
            if (data.users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px;">暂无用户</td></tr>';
            } else {
                data.users.forEach(user => {
                    const role = user.is_admin ? '管理员' : '普通用户';
                    const badgeClass = user.is_admin ? 'badge-admin' : 'badge-user';
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${user.username}</td>
                        <td>${user.email || '-'}</td>
                        <td><span class="badge ${badgeClass}">${role}</span></td>
                        <td>${user.created_at || '-'}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-info btn-sm" onclick="editUser('${user.username}', '${user.email || ''}', ${user.is_admin})">
                                    <i class="fas fa-edit"></i> 编辑
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="deleteUser('${user.username}')" ${user.username === 'admin' ? 'disabled' : ''}>
                                    <i class="fas fa-trash"></i> 删除
                                </button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        } else {
            showMessage(data.error || '加载失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Load users error:', error);
    } finally {
        hideLoading();
    }
}

// 刷新用户列表
function refreshUsers() {
    loadUsers();
}

// 编辑用户
function editUser(username, email, isAdmin) {
    document.getElementById('editUsername').value = username;
    document.getElementById('editUsername').disabled = true; // 编辑时禁用用户名
    document.getElementById('editEmail').value = email;
    document.getElementById('editRole').value = isAdmin ? 'admin' : 'user';
    document.getElementById('editPassword').value = '';
    document.getElementById('passwordLabel').textContent = '新密码 (留空不修改):';
    document.querySelector('#editUserModal h2').textContent = '编辑用户';
    document.getElementById('editUserModal').style.display = 'block';
}

// 关闭编辑模态框
function closeEditModal() {
    document.getElementById('editUserModal').style.display = 'none';
}

// 保存用户编辑
async function saveUserEdit() {
    const username = document.getElementById('editUsername').value;
    const email = document.getElementById('editEmail').value;
    const role = document.getElementById('editRole').value;
    const password = document.getElementById('editPassword').value;
    
    const updateData = {
        email: email,
        is_admin: role === 'admin'
    };
    
    if (password) {
        updateData.password = password;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`/api/admin/users/${username}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('用户信息已更新', 'success');
            closeEditModal();
            loadUsers();
        } else {
            showMessage(data.error || '更新失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Update user error:', error);
    } finally {
        hideLoading();
    }
}

// 删除用户
async function deleteUser(username) {
    if (!confirm(`确定要删除用户 "${username}" 吗？此操作不可恢复！`)) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`/api/admin/users/${username}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message || '用户已删除', 'success');
            loadUsers();
        } else {
            showMessage(data.error || '删除失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Delete user error:', error);
    } finally {
        hideLoading();
    }
}

// 加载统计信息
async function loadStatistics() {
    showLoading();
    try {
        const response = await fetch('/api/admin/statistics');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.statistics;
            
            // 更新统计卡片
            document.getElementById('totalUsers').textContent = stats.users.total;
            document.getElementById('adminCount').textContent = stats.users.admins;
            document.getElementById('totalRecords').textContent = stats.records.total;
            document.getElementById('overallAccuracy').textContent = stats.records.accuracy.toFixed(2) + '%';
            
            // 更新活动表格
            const activityBody = document.getElementById('activityTableBody');
            activityBody.innerHTML = '';
            
            if (stats.recent_activity.length === 0) {
                activityBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px;">暂无活动记录</td></tr>';
            } else {
                stats.recent_activity.forEach(activity => {
                    const status = activity.success ? '✓' : '✗';
                    const statusColor = activity.success ? '#10b981' : '#ef4444';
                    const statusBadge = activity.success ? 'badge-success' : 'badge-danger';
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${activity.user || 'unknown'}</td>
                        <td>${activity.timestamp || '-'}</td>
                        <td>${activity.action || '-'}</td>
                        <td>${activity.method || '-'}</td>
                        <td><span class="badge ${statusBadge}">${status}</span></td>
                    `;
                    activityBody.appendChild(row);
                });
            }
        } else {
            showMessage(data.error || '加载失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Load statistics error:', error);
    } finally {
        hideLoading();
    }
}

// 刷新统计信息
function refreshStatistics() {
    loadStatistics();
}

// 加载存储信息
async function loadStorage() {
    showLoading();
    try {
        const response = await fetch('/api/admin/statistics');
        const data = await response.json();
        
        if (data.success) {
            const storage = data.statistics.storage;
            document.getElementById('captchaFiles').textContent = storage.captcha_files;
            document.getElementById('captchaSize').textContent = storage.captcha_size_mb;
            document.getElementById('modelFiles').textContent = storage.model_files;
            document.getElementById('modelSize').textContent = storage.model_size_mb;
        } else {
            showMessage(data.error || '加载失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Load storage error:', error);
    } finally {
        hideLoading();
    }
}

// 刷新存储信息
function refreshStorage() {
    loadStorage();
}

// 加载日志
async function loadLogs() {
    showLoading();
    try {
        const response = await fetch('/api/admin/logs');
        const data = await response.json();
        
        if (data.success) {
            const logsBody = document.getElementById('logsTableBody');
            logsBody.innerHTML = '';
            
            if (data.logs.length === 0) {
                logsBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px;">暂无日志</td></tr>';
            } else {
                data.logs.forEach(log => {
                    const statusBadge = log.success ? 'badge-success' : 'badge-danger';
                    const status = log.success ? '✓' : '✗';
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${log.timestamp || '-'}</td>
                        <td>${log.user || '-'}</td>
                        <td>${log.action || '-'}</td>
                        <td>${log.method || '-'}</td>
                        <td><span class="badge ${statusBadge}">${status}</span></td>
                    `;
                    logsBody.appendChild(row);
                });
            }
        } else {
            showMessage(data.error || '加载失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Load logs error:', error);
    } finally {
        hideLoading();
    }
}

// 刷新日志
function refreshLogs() {
    loadLogs();
}

// 清理数据
async function cleanupData(type) {
    const typeNames = {
        'captchas': '验证码文件',
        'history': '历史记录',
        'models': '模型文件',
        'all': '所有数据'
    };
    
    const typeName = typeNames[type] || type;
    
    if (!confirm(`确定要清理 ${typeName} 吗？此操作不可恢复！`)) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/admin/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: type })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`清理完成: ${data.cleaned.join(', ')}`, 'success');
            // 刷新相关数据
            if (type === 'all' || type === 'captchas') {
                refreshStorage();
            }
            if (type === 'all' || type === 'history') {
                refreshStatistics();
            }
        } else {
            showMessage(data.error || '清理失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Cleanup error:', error);
    } finally {
        hideLoading();
    }
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('editUserModal');
    if (event.target === modal) {
        closeEditModal();
    }
}

// 显示/隐藏加载提示
function showLoading() {
    document.getElementById('loading').classList.add('show');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('show');
}

// 显示消息
function showMessage(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '20px';
    messageDiv.style.right = '20px';
    messageDiv.style.zIndex = '4000';
    messageDiv.style.minWidth = '300px';
    messageDiv.style.padding = '15px 20px';
    messageDiv.style.borderRadius = '10px';
    messageDiv.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        messageDiv.style.transition = 'opacity 0.3s';
        setTimeout(() => {
            document.body.removeChild(messageDiv);
        }, 300);
    }, 3000);
}

// 加载历史记录
async function loadHistory() {
    showLoading();
    try {
        const usernameFilter = document.getElementById('historyUserFilter').value;
        const url = usernameFilter 
            ? `/api/admin/history?username=${encodeURIComponent(usernameFilter)}`
            : '/api/admin/history';
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            // 更新用户筛选下拉框
            const filterSelect = document.getElementById('historyUserFilter');
            if (filterSelect.children.length === 1) {
                // 首次加载，填充用户列表
                data.users.forEach(username => {
                    const option = document.createElement('option');
                    option.value = username;
                    option.textContent = username;
                    filterSelect.appendChild(option);
                });
            }
            
            const tbody = document.getElementById('historyTableBody');
            tbody.innerHTML = '';
            
            if (data.history.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">暂无历史记录</td></tr>';
            } else {
                data.history.forEach(record => {
                    const status = record.success ? '✓' : '✗';
                    const statusBadge = record.success ? 'badge-success' : 'badge-danger';
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${record.timestamp || '-'}</td>
                        <td>${record.user || '-'}</td>
                        <td>${record.captcha || '-'}</td>
                        <td>${record.recognized || '-'}</td>
                        <td>${record.method || '-'}</td>
                        <td>${record.difficulty || '-'}</td>
                        <td><span class="badge ${statusBadge}">${status}</span></td>
                    `;
                    tbody.appendChild(row);
                });
            }
        } else {
            showMessage(data.error || '加载失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Load history error:', error);
    } finally {
        hideLoading();
    }
}

// 显示添加用户模态框
function showAddUserModal() {
    document.getElementById('editUsername').value = '';
    document.getElementById('editUsername').disabled = false; // 添加时启用用户名
    document.getElementById('editEmail').value = '';
    document.getElementById('editRole').value = 'user';
    document.getElementById('editPassword').value = '';
    document.getElementById('passwordLabel').textContent = '密码:';
    document.querySelector('#editUserModal h2').textContent = '添加用户';
    document.getElementById('editUserModal').style.display = 'block';
}

// 保存用户编辑（支持添加和编辑）
async function saveUserEdit() {
    const username = document.getElementById('editUsername').value.trim();
    const email = document.getElementById('editEmail').value.trim();
    const role = document.getElementById('editRole').value;
    const password = document.getElementById('editPassword').value;
    
    if (!username) {
        showMessage('请输入用户名', 'error');
        return;
    }
    
    const isEdit = document.querySelector('#editUserModal h2').textContent === '编辑用户';
    
    if (isEdit) {
        // 编辑模式
        const updateData = {
            email: email,
            is_admin: role === 'admin'
        };
        
        if (password) {
            updateData.password = password;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`/api/admin/users/${username}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage('用户信息已更新', 'success');
                closeEditModal();
                loadUsers();
            } else {
                showMessage(data.error || '更新失败', 'error');
            }
        } catch (error) {
            showMessage('网络错误，请重试', 'error');
            console.error('Update user error:', error);
        } finally {
            hideLoading();
        }
    } else {
        // 添加模式
        if (!password) {
            showMessage('请输入密码', 'error');
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 如果是管理员角色，需要更新
                if (role === 'admin') {
                    const updateResponse = await fetch(`/api/admin/users/${username}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            email: email,
                            is_admin: true
                        })
                    });
                    await updateResponse.json();
                }
                
                showMessage('用户添加成功', 'success');
                closeEditModal();
                loadUsers();
            } else {
                showMessage(data.message || '添加失败', 'error');
            }
        } catch (error) {
            showMessage('网络错误，请重试', 'error');
            console.error('Add user error:', error);
        } finally {
            hideLoading();
        }
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 默认加载用户管理
    loadUsers();
});

