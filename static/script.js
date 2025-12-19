
function togglePerformer(performerId) {
    fetch(`/api/performer/${performerId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при изменении статуса');
    });
}

document.getElementById('addPerformerForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const name = document.getElementById('name').value;
    const role = document.getElementById('role').value;
    const skill = document.getElementById('skill').value || 5;
    
    fetch('/api/add_performer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: name,
            role: role,
            skill_level: parseInt(skill)
        })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при добавлении артиста');
    });
});

function performAction(performerId) {
    fetch(`/api/performer/${performerId}`)
    .then(response => response.json())
    .then(performer => {
        const messages = [
            `${performer.name} начинает выступление!`,
            `${performer.name} показывает ${performer.skill_level > 7 ? 'великолепный' : 'хороший'} трюк!`,
            `Аплодисменты для ${performer.name}!`,
            `${performer.name} завершает выступление. Браво!`
        ];
        
        const resultDiv = document.getElementById('performanceResult');
        resultDiv.innerHTML = `
            <div class="performance-message">
                <h3>🎪 Выступление ${performer.name}</h3>
                <p>${messages[Math.floor(Math.random() * messages.length)]}</p>
                <p><em>Роль: ${performer.role} | Уровень: ${performer.skill_level}/10</em></p>
            </div>
        `;
        resultDiv.style.animation = 'fadeIn 0.5s ease-out';
    });
}

function trainPerformer(performerId) {
    fetch(`/api/performer/${performerId}`)
    .then(response => response.json())
    .then(performer => {
        const resultDiv = document.getElementById('performanceResult');
        resultDiv.innerHTML = `
            <div class="training-message">
                <h3>🏋️ ${performer.name} тренируется</h3>
                <p>${performer.name} улучшает свои навыки ${performer.role}а!</p>
                <p>Новый уровень навыка: ${Math.min(10, performer.skill_level + 1)}/10</p>
            </div>
        `;
        
        // Обновляем уровень на странице
        const skillElement = document.querySelector('.skill-level');
        if (skillElement) {
            const newSkill = Math.min(10, performer.skill_level + 1);
            skillElement.textContent = `${newSkill}/10`;
            document.querySelector('progress').value = newSkill;
        }
    });
}