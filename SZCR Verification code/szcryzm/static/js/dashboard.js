// 全局变量
let currentCaptchaImage = null;

// 生成验证码
async function generateCaptcha(difficulty, length) {
    showLoading();
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ difficulty, length })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 显示验证码图像
            const imageContainer = document.getElementById('captchaImage');
            imageContainer.innerHTML = `<img src="${data.image}" alt="验证码">`;
            
            // 更新文本
            document.getElementById('captchaText').textContent = data.text;
            document.getElementById('recognitionResult').textContent = '未识别';
            document.getElementById('recognitionResult').style.color = '#6b7280';
            
            // 保存当前图像数据
            currentCaptchaImage = data.image;
        } else {
            showMessage(data.error || '生成失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Generate error:', error);
    } finally {
        hideLoading();
    }
}

// 识别验证码
async function recognizeCaptcha(method) {
    if (!currentCaptchaImage) {
        showMessage('请先生成验证码', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/recognize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                method: method,
                image: currentCaptchaImage
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const resultElement = document.getElementById('recognitionResult');
            resultElement.textContent = data.result;
            
            if (data.match) {
                resultElement.style.color = '#10b981';
                showMessage(`识别正确！结果: ${data.result}`, 'success');
            } else {
                resultElement.style.color = '#ef4444';
                showMessage(`识别错误。结果: ${data.result}，正确答案: ${data.correct}`, 'error');
            }
        } else {
            showMessage(data.error || '识别失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Recognize error:', error);
    } finally {
        hideLoading();
    }
}

// 验证用户输入
async function validateInput() {
    const input = document.getElementById('manualInput').value.trim();
    
    if (!input) {
        showMessage('请输入验证码', 'error');
        return;
    }
    
    if (!currentCaptchaImage) {
        showMessage('请先生成验证码', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ input })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('recognitionResult').textContent = input;
            document.getElementById('recognitionResult').style.color = '#10b981';
            showMessage(data.message, 'success');
        } else {
            document.getElementById('recognitionResult').textContent = input;
            document.getElementById('recognitionResult').style.color = '#ef4444';
            showMessage(data.message, 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Validate error:', error);
    } finally {
        hideLoading();
    }
}

// 批量生成对话框
function showBatchDialog() {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <div class="modal-body">
            <h2 style="margin-bottom: 20px;">批量生成验证码</h2>
            <div class="form-group">
                <label>生成数量:</label>
                <input type="number" id="batchCount" class="form-control" value="10" min="1" max="100">
            </div>
            <div class="form-group">
                <label>验证码长度:</label>
                <input type="number" id="batchLength" class="form-control" value="5" min="4" max="8">
            </div>
            <div class="form-group">
                <label>难度:</label>
                <select id="batchDifficulty" class="form-control">
                    <option value="simple">简单</option>
                    <option value="medium" selected>中等</option>
                    <option value="hard">困难</option>
                </select>
            </div>
            <div style="margin-top: 20px; display: flex; gap: 10px;">
                <button class="btn btn-primary" onclick="startBatchGenerate()">开始生成</button>
                <button class="btn btn-secondary" onclick="closeModal()">取消</button>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
}

// 开始批量生成
async function startBatchGenerate() {
    const count = parseInt(document.getElementById('batchCount').value);
    const length = parseInt(document.getElementById('batchLength').value);
    const difficulty = document.getElementById('batchDifficulty').value;
    
    if (count < 1 || count > 100) {
        showMessage('生成数量应在1-100之间', 'error');
        return;
    }
    
    closeModal();
    showLoading();
    
    try {
        const response = await fetch('/api/batch_generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ count, length, difficulty })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`成功生成 ${data.count} 个验证码！保存位置: ${data.folder}`, 'success');
        } else {
            showMessage(data.error || '批量生成失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Batch generate error:', error);
    } finally {
        hideLoading();
    }
}

// 显示历史记录
async function showHistory() {
    showLoading();
    
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.success) {
            const modal = document.getElementById('modal');
            const modalBody = document.getElementById('modalBody');
            
            let tableHTML = `
                <div class="modal-body">
                    <h2 style="margin-bottom: 20px;">历史记录</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>时间</th>
                                    <th>验证码</th>
                                    <th>识别结果</th>
                                    <th>方法</th>
                                    <th>难度</th>
                                    <th>状态</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            if (data.history.length === 0) {
                tableHTML += '<tr><td colspan="6" style="text-align: center; padding: 40px;">暂无历史记录</td></tr>';
            } else {
                data.history.reverse().forEach(record => {
                    const status = record.success ? '✓' : '✗';
                    const statusColor = record.success ? '#10b981' : '#ef4444';
                    tableHTML += `
                        <tr>
                            <td>${record.timestamp}</td>
                            <td>${record.captcha}</td>
                            <td>${record.recognized}</td>
                            <td>${record.method}</td>
                            <td>${record.difficulty}</td>
                            <td style="color: ${statusColor}; font-weight: bold;">${status}</td>
                        </tr>
                    `;
                });
            }
            
            tableHTML += `
                            </tbody>
                        </table>
                    </div>
                    <div style="margin-top: 20px; text-align: right;">
                        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
                    </div>
                </div>
            `;
            
            modalBody.innerHTML = tableHTML;
            modal.style.display = 'block';
        } else {
            showMessage(data.error || '获取历史记录失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('History error:', error);
    } finally {
        hideLoading();
    }
}

// 显示统计信息
async function showStatistics() {
    showLoading();
    
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.statistics;
            const modal = document.getElementById('modal');
            const modalBody = document.getElementById('modalBody');
            
            let statsHTML = `
                <div class="modal-body">
                    <h2 style="margin-bottom: 20px;">统计信息</h2>
                    <div style="font-size: 16px; line-height: 2;">
                        <p><strong>总验证次数:</strong> ${stats.total}</p>
                        <p><strong>成功次数:</strong> ${stats.success}</p>
                        <p><strong>总体准确率:</strong> <span style="color: #10b981; font-weight: bold;">${(stats.accuracy * 100).toFixed(2)}%</span></p>
            `;
            
            if (stats.by_difficulty && Object.keys(stats.by_difficulty).length > 0) {
                statsHTML += '<h3 style="margin-top: 20px; margin-bottom: 10px;">按难度统计:</h3>';
                for (const [diff, diffStats] of Object.entries(stats.by_difficulty)) {
                    const accuracy = (diffStats.accuracy * 100).toFixed(2);
                    statsHTML += `<p><strong>${diff}:</strong> ${diffStats.success}/${diffStats.total} = <span style="color: #10b981;">${accuracy}%</span></p>`;
                }
            }
            
            if (stats.by_method && Object.keys(stats.by_method).length > 0) {
                statsHTML += '<h3 style="margin-top: 20px; margin-bottom: 10px;">按方法统计:</h3>';
                for (const [method, methodStats] of Object.entries(stats.by_method)) {
                    const accuracy = (methodStats.accuracy * 100).toFixed(2);
                    statsHTML += `<p><strong>${method}:</strong> ${methodStats.success}/${methodStats.total} = <span style="color: #10b981;">${accuracy}%</span></p>`;
                }
            }
            
            statsHTML += `
                    </div>
                    <div style="margin-top: 20px; text-align: right;">
                        <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
                    </div>
                </div>
            `;
            
            modalBody.innerHTML = statsHTML;
            modal.style.display = 'block';
        } else {
            showMessage(data.error || '获取统计信息失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Statistics error:', error);
    } finally {
        hideLoading();
    }
}

// 训练模型对话框
function showTrainDialog() {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <div class="modal-body">
            <h2 style="margin-bottom: 20px;">训练机器学习模型</h2>
            <div class="form-group">
                <label>数据集路径:</label>
                <input type="text" id="datasetPath" class="form-control" value="data/dataset">
            </div>
            <div class="form-group">
                <label>模型类型:</label>
                <select id="modelType" class="form-control">
                    <option value="knn" selected>KNN (K近邻)</option>
                    <option value="svm">SVM (支持向量机)</option>
                    <option value="random_forest">Random Forest (随机森林)</option>
                </select>
            </div>
            <div style="margin-top: 20px; display: flex; gap: 10px;">
                <button class="btn btn-primary" onclick="startTrain()">开始训练</button>
                <button class="btn btn-secondary" onclick="closeModal()">取消</button>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
}

// 开始训练
async function startTrain() {
    const datasetPath = document.getElementById('datasetPath').value.trim();
    const modelType = document.getElementById('modelType').value;
    
    if (!datasetPath) {
        showMessage('请输入数据集路径', 'error');
        return;
    }
    
    closeModal();
    showLoading();
    
    try {
        const response = await fetch('/api/train', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dataset_path: datasetPath, model_type: modelType })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`训练完成！准确率: ${(data.accuracy * 100).toFixed(2)}%`, 'success');
        } else {
            showMessage(data.error || '训练失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Train error:', error);
    } finally {
        hideLoading();
    }
}

// 清空历史记录
async function clearHistory() {
    if (!confirm('确定要清空所有历史记录吗？此操作不可恢复！')) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/clear_history', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('历史记录已清空', 'success');
        } else {
            showMessage(data.error || '清空失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
        console.error('Clear history error:', error);
    } finally {
        hideLoading();
    }
}

// 关闭模态框
function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('modal');
    if (event.target === modal) {
        closeModal();
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
    // 创建消息元素
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

// 回车键提交手动验证
document.getElementById('manualInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        validateInput();
    }
});

