document.addEventListener('DOMContentLoaded', function () {
  const usernameInput = document.getElementById('username');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const passwordConfirm = document.getElementById('password-confirm');
  const form = document.getElementById('settings-form');
  const deleteBtn = document.getElementById('delete-account');

  if (window.CURRENT_USER) {
    usernameInput.value = window.CURRENT_USER.username || '';
    emailInput.value = window.CURRENT_USER.email || '';
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const username = usernameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirm = passwordConfirm.value;

    if (password && password !== confirm) {
      alert('As senhas não conferem');
      return;
    }

    const payload = { username, email };
    if (password) payload.password = password;

    try {
      const res = await fetch('/api/update-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'same-origin'
      });
      const data = await res.json();
      alert(data.msg || 'Atualizado com sucesso');
      location.reload();
    } catch (err) {
      console.error(err);
      alert('Erro ao atualizar. Tente novamente.');
    }
  });

  deleteBtn.addEventListener('click', async function () {
    const ok = confirm('Deseja realmente excluir sua conta? Esta ação é irreversível.');
    if (!ok) return;
    const senha = prompt('Confirme sua senha para excluir a conta:');
    if (!senha) return;

    try {
      const res = await fetch('/api/delete-user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ senha }),
        credentials: 'same-origin'
      });
      const data = await res.json();
      alert(data.msg || 'Operação concluída');
      if (data.msg && data.msg.toLowerCase().includes('delet')) {
        window.location.href = '/login';
      }
    } catch (err) {
      console.error(err);
      alert('Erro ao excluir. Tente novamente.');
    }
  });

});
