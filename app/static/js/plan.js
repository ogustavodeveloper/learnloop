Swal.fire({
  title: 'Conheça o Sessão de Estudos',
  text: "Preparado para elevar sua organização e produtividade nos estudos? Aqui, você tem controle total sobre o que estuda. Inicie o cronômetro, faça anotações e, se necessário, clique em 'Aprimorar anotação com IA' para uma versão mais estruturada. Salve suas sessões de estudo, revise suas anotações e compartilhe seu progresso. Aproveite ao máximo!",
  icon: 'info'
});

document.addEventListener('DOMContentLoaded', function() {
  let tempoEstudado = '00:00:00';
  let cronometroInterval;
  let cronometroRodando = false;

  function formatarTempo(horas, minutos, segundos) {
    return `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
  }

  function iniciarCronometro() {
    if (!localStorage.getItem('inicioCronometro')) {
      localStorage.setItem('inicioCronometro', Date.now());
    }

    cronometroInterval = setInterval(function() {
      let inicio = parseInt(localStorage.getItem('inicioCronometro'));
      let agora = Date.now();
      let diferenca = agora - inicio;

      let segundosTotais = Math.floor(diferenca / 1000);
      let horas = Math.floor(segundosTotais / 3600);
      let minutos = Math.floor((segundosTotais % 3600) / 60);
      let segundos = segundosTotais % 60;

      tempoEstudado = formatarTempo(horas, minutos, segundos);
      document.getElementById('tempo-estudado').innerText = tempoEstudado;
    }, 1000);

    cronometroRodando = true;
    localStorage.setItem('cronometroRodando', 'true');
  }

  function pausarCronometro() {
    clearInterval(cronometroInterval);
    cronometroRodando = false;
    localStorage.setItem('cronometroRodando', 'false');
  }

  function pararCronometro() {
    clearInterval(cronometroInterval);
    tempoEstudado = '00:00:00';
    document.getElementById('tempo-estudado').innerText = tempoEstudado;
    cronometroRodando = false;
    localStorage.removeItem('inicioCronometro');
    localStorage.setItem('cronometroRodando', 'false');
  }

  // Verifica se o cronômetro estava rodando ao recarregar a página
  if (localStorage.getItem('cronometroRodando') === 'true') {
    iniciarCronometro();
    document.querySelector('button#iniciar').textContent = 'Pausar';
  }

  const iniciarBtn = document.querySelector('button#iniciar');
  iniciarBtn.addEventListener('click', function() {
    if (!cronometroRodando) {
      iniciarCronometro();
      iniciarBtn.textContent = 'Pausar';
    } else {
      pausarCronometro();
      iniciarBtn.textContent = 'Continuar';
    }
  });

  const pararBtn = document.querySelector('button#parar');
  pararBtn.addEventListener('click', function() {
    pararCronometro();
    iniciarBtn.textContent = 'Iniciar';
  });

  const aprimorarBtn = document.querySelector('button#aprimorar');
  aprimorarBtn.addEventListener('click', function() {
    const resumo = document.querySelector('textarea#resumo').value;
    document.querySelector("#resumo").value = "Aguarda um pouquinho!";

    axios.post('/api/get-resumo-ia', { notes: resumo })
      .then(function(response) {
        const novoResumo = response.data.msg;
        document.querySelector('textarea#resumo').value = novoResumo;
      })
      .catch(function(error) {
        console.error('Erro ao aprimorar as anotações:', error);
      });
  });

  const salvarBtn = document.querySelector('button#salvar');
  salvarBtn.addEventListener('click', function() {
    const assunto = document.querySelector('#assunto').value;

    axios.post('/save-session', {
      assunto: assunto,
      tempo: tempoEstudado,
      resumo: document.querySelector("#resumo").value
    })
      .then(function(response) {
        Swal.fire({
          icon: 'success',
          title: 'Sessão de estudos salva!',
          text: `${response.data.msg}`,
          showConfirmButton: false,
          timer: 1500
        });
      })
      .catch(function(error) {
        console.error('Erro ao salvar a sessão de estudos:', error);
      });
  });

  const sessoes = document.querySelectorAll('.sessao-estudos');
  sessoes.forEach(function(sessao) {
    sessao.addEventListener('click', function() {
      const resumo = sessao.getAttribute('data-resumo');
      const assunto = sessao.getAttribute('data-assunto');
      const dia = sessao.getAttribute('data-dia');
      const tempo = sessao.getAttribute('data-tempo');

      Swal.fire({
        title: 'Detalhes da Sessão de Estudos',
        html: `
          <p><strong>Assunto:</strong> ${assunto}</p>
          <p><strong>Dia:</strong> ${dia}</p>
          <p><strong>Tempo Estudado:</strong> ${tempo}</p>
          <p><strong>Anotação:</strong> ${resumo}</p>
        `,
        icon: 'info',
        confirmButtonText: 'Fechar'
      });
    });
  });
});
