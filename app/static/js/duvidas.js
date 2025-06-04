function search() {
  var search = prompt("Digite o que você quer pesquisar:")
  if(search == false) {
    return;
  } else {
    axios.get("/search/artigos?pesquisa="+search)
  }
}

function excluirConta() {
  var senha = prompt("Digite sua senha para deletar sua conta:")
  if(senha === false) {
    return;
  } else {
    axios.post("/api/delete-user", {
      "senha": senha
    }).then((r) => {
      if(r.data.msg === "usuario deletado com sucesso") {
        window.location.href = "/login"
      } else {
        Swal.fire({
          title: 'Erro!',
          text: 'Senha incorreta!',
          icon: 'error',
        });
      }
    })
  }
}

function ajudaDinamica() {
  const path = window.location.pathname;

  let titulo = 'Ajuda';
  let html = 'Aqui você encontra informações sobre o uso da plataforma.';

  if (path.includes('/duvidas')) {
    titulo = 'Como funciona a página de Dúvidas?';
    html = `
      <b>Publicar Dúvida:</b> Clique em "Publicar Dúvida", escreva sua dúvida e confirme.<br><br>
      <b>Responder:</b> Clique em "Responder Dúvida" para enviar uma resposta.<br><br>
      <b>Visualizar:</b> Clique no texto da dúvida para ver detalhes e respostas.<br><br>
      <b>Deletar:</b> Dentro dos detalhes, use "Deletar Dúvida" para remover.<br><br>
      <i>Use esta página para compartilhar e resolver dúvidas com outros usuários!</i>
    `;
  } else if (path.startsWith('/feed-session') || path.startsWith('/feed-sessions')) {
    titulo = 'Como funciona a Lista de Sessões de Estudos?';
    html = `
      <b>Registrar Nova Sessão:</b> Clique em "Registrar Nova Sessão" para criar uma nova sessão de estudos.<br><br>
      <b>Visualizar Sessão:</b> Clique em uma sessão para ver detalhes, anotações e documentos.<br><br>
      <i>Organize e acesse rapidamente todas as suas sessões de estudo!</i>
    `;
  } else if (path.startsWith('/session')) {
    titulo = 'Como funciona a página de Sessão de Estudos?';
    html = `
      <b>Resumo/Anotações:</b> Escreva ou edite suas anotações e clique em "Atualizar Anotação".<br><br>
      <b>Adicionar Arquivo:</b> Selecione um arquivo e clique em "Adicionar" para anexar materiais.<br><br>
      <b>Documentos Salvos:</b> Clique nos nomes dos arquivos para abri-los.<br><br>
      <b>Quizzes:</b> Veja quizzes já criados ou clique em "Gerar Quiz" para criar um novo.<br><br>
      <b>Deletar Sessão:</b> Use o botão ao final para excluir esta sessão.<br><br>
      <i>Organize seus estudos, salve materiais e teste seus conhecimentos!</i>
    `;
  } else if (path.startsWith('/redacoes')) {
    titulo = 'Como funciona a página de Redações Corrigidas?';
    html = `
      <b>Visualizar Correção:</b> Clique no tema de uma redação para ver a correção detalhada.<br><br>
      <b>Nova Correção:</b> Clique em "Corrigir Nova Redação" para enviar outro texto.<br><br>
      <i>Acompanhe seu progresso e veja o feedback das suas redações!</i>
    `;
  } else if (path.startsWith('/correcao/')) {
    titulo = 'Como funciona a Correção de Redação?';
    html = `
      <b>Correção Detalhada:</b> Veja a análise de cada competência do ENEM.<br><br>
      <b>Nota Final:</b> Confira sua nota final e o comentário geral.<br><br>
      <i>Use o feedback para aprimorar sua redação e focar nos pontos que precisam de atenção!</i>
    `;
  } else if (path.startsWith('/avaliar-redacao')) {
    titulo = 'Como funciona a Redação Guiada?';
    html = `
      <b>Redação Guiada:</b> Clique em "Redação Guiada" para receber dicas personalizadas sobre o que escrever a seguir.<br><br>
      <b>Correção Automática:</b> Envie sua redação para receber uma correção detalhada por competência.<br><br>
      <b>Digitalizar Redação:</b> Use a opção de digitalizar para enviar uma foto do seu texto manuscrito.<br><br>
      <i>Aproveite para evoluir sua escrita com o apoio da IA!</i>
    `;
  } else if (path.includes('/artigos')) {
    titulo = 'Como funciona a página de Artigos?';
    html = `
      <b>Pesquisar:</b> Use a barra de pesquisa para encontrar artigos.<br><br>
      <b>Visualizar:</b> Clique no título de um artigo para ler.<br><br>
      <b>Salvar:</b> Adicione artigos aos favoritos para acessar depois.<br><br>
      <i>Explore conteúdos para aprofundar seus estudos!</i>
    `;
  }

  Swal.fire({
    title: titulo,
    html: html,
    icon: 'info',
    confirmButtonText: 'Entendi!'
  });
}

// Adiciona o evento ao botão de ajuda, se existir
document.addEventListener('DOMContentLoaded', function() {
  const btnAjuda = document.querySelector('#help-icon');
  if (btnAjuda) {
    btnAjuda.onclick = ajudaDinamica; // Sem parênteses!
  }
});