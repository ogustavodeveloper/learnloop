function redacao() {
  var titulo = document.getElementById("titulo");
  var tema = document.getElementById("tema_custom");
  var conteudo = document.getElementById("conteudo");

  if (titulo && titulo.value.length < 5) {
    Swal.fire({
      title: "Erro",
      text: "O título da redação deve ter no mínimo 5 caracteres.",
      icon: "error"
    });
    return;
  }

  if (!tema || tema.value.length < 5) {
    Swal.fire({
      title: "Erro",
      text: "O tema da redação deve ter no mínimo 5 caracteres.",
      icon: "error"
    });
    return;
  }

  if (conteudo.value.length < 20) {
    Swal.fire({
      title: "Erro",
      text: "O conteúdo da redação deve ter no mínimo 20 caracteres.",
      icon: "error"
    });
    return;
  }

  Swal.fire({
    title: "Corrigindo sua redação...",
    text: "Aguarde, em instantes você será redirecionado para uma página com a correção detalhada.",
    icon: "info"
  });

  axios.post("/learn-ai/redacao", {
    title: titulo ? titulo.value : "",
    content: conteudo.value,
    nivel: document.getElementById("nivel").value,
    tema: tema.value
  }).then((r) => {
    if (r.data.msg === "success") {
      window.location.href = '/correcao/' + r.data.response;
    } else {
      Swal.fire({
        title: "Erro ao corrigir sua redação",
        text: `Tire um print da mensagem ao lado e mande para o Instagram do Estudaê (@estudae.of) para podermos resolver este erro: ${r.data.details}`,
        icon: 'error'
      });
    }
  }).catch((error) => {
    Swal.fire({
      title: "Houve um erro ao corrigir a sua redacão.",
      text: `Tire um print da mensagem ao lado e mande para o Instagram do Estudaê (@estudae.of) para podermos resolver este erro: ${error}`,
      icon: "error"
    });
    console.error("Erro:", error);
  });
}

Swal.fire({
  title: "Corretor de Redação",
  text: "Envie sua redação digitada ou por foto e receba orientações do Learn.Ai. Se ficar travado, clique em Redação Guiada para receber uma dica personalizada.",
  icon: 'info'
});

function carregarFoto() {
  Swal.fire({
    title: "Carregar Foto",
    description: "Faça o upload da foto de seu caderno aqui",
    html: `
      <input type="file" id="foto" >
    `,
    preConfirm: () => {
      const formData = new FormData();
      var foto = document.getElementById("foto");
      formData.append("foto", foto.files[0]);

      return axios.post("/api/carregar-redacao", formData, {
        headers: {
          "Content-Type": `multipart/form-data; boundary=${formData._boundary}`
        }
      }).then((f) => {
        if (f.data.msg === "success") {
          document.getElementById("conteudo").value += f.data.redacao;
        }
      }).catch((error) => {
        Swal.fire({
          title: "Erro ao carregar sua foto",
          text: "Verifique se o arquivo está nos formatos: '.png, .jpeg, jpg' e tente novamente.",
          icon: "error"
        })
      });
    }
  });
}

function salvarRedacao() {
  var titulo = document.getElementById("titulo").value;
  var texto = document.getElementById("conteudo").value;

  Swal.fire({
    title: "Salvando sua redação...",
    text: "Por favor, aguarde.",
    icon: "info",
    allowOutsideClick: false,
    showConfirmButton: false,
    didOpen: () => {
      Swal.showLoading();

      axios.post("/api/save-redacao", {
        titulo: titulo,
        texto: texto
      }).then((response) => {
        Swal.close();
        if (response.data.msg === "success") {
          Swal.fire({
            title: "Sucesso!",
            text: "Redação salva com sucesso.",
            icon: "success",
            confirmButtonText: "OK"
          });
        } else {
          Swal.fire({
            title: "Erro",
            text: "Erro ao salvar a redação.",
            icon: "error",
            confirmButtonText: "Tentar novamente"
          });
        }
      }).catch((error) => {
        Swal.close();
        Swal.fire({
          title: "Erro",
          text: "Ocorreu um erro ao tentar salvar sua redação.",
          icon: "error",
          confirmButtonText: "Tentar novamente"
        });
        console.error("Erro:", error);
      });
    }
  });
}

function redacaoGuiada() {
  var tema = document.getElementById("tema_custom").value;
  var texto = document.getElementById("conteudo").value;
  

  if (tema.length < 5) {
    Swal.fire({
      title: "Erro",
      text: "O tema da redação deve ter no mínimo 5 caracteres.",
      icon: "error"
    });
    return;
  }

  if (texto.length < 5) {    
    Swal.fire({
      title: "Erro",
      text: "O conteúdo da redação deve ter no mínimo 5 caracteres.",  
      icon: "error"
    });
    return;
  }


  // Pergunta ao usuário usando HTML com rádios (evita problema de fundo branco)
  Swal.fire({
    title: 'Em qual estágio está sua redação?',
    html: `
      <div style="text-align:left">
        <label style="display:block; margin:8px 0;"><input type="radio" name="estagioRadio" value="Introdução"> Introdução</label>
        <label style="display:block; margin:8px 0;"><input type="radio" name="estagioRadio" value="Desenvolvimento"> Desenvolvimento</label>
        <label style="display:block; margin:8px 0;"><input type="radio" name="estagioRadio" value="Conclusão"> Conclusão</label>
      </div>
    `,
    focusConfirm: false,
    showCancelButton: true,
    preConfirm: () => {
      const checked = document.querySelector('input[name="estagioRadio"]:checked');
      if (!checked) {
        Swal.showValidationMessage('Selecione o estágio da redação');
        return false;
      }
      return checked.value;
    }
  }).then((result) => {
    if (!result.isConfirmed) return;
    var estagio = result.value;

    // Exibir alerta de carregamento
    Swal.fire({
      title: 'Carregando...',
      text: 'Aguarde enquanto processamos sua redação.',
      allowOutsideClick: false,
      didOpen: () => {
        Swal.showLoading();
      }
    });

    axios.post("/api/redacao-guiada", {
      tema: tema,
      texto: texto,
      estagio: estagio
    }).then((response) => {
      var data = response.data;
      // Fechar o alerta de carregamento
      Swal.close();

      if (data.msg === "success") {
        Swal.fire({
          title: "Redação Guiada",
          text: data.guia
        });
      }
    }).catch((error) => {
      // Fechar o alerta de carregamento em caso de erro
      Swal.close();

      Swal.fire({
        title: 'Erro!',
        text: 'Ocorreu um erro ao processar sua solicitação.',
        icon: 'error'
      });
    });
  });
}

// Sincroniza o select de temas com o input de tema_custom
document.addEventListener('DOMContentLoaded', function() {
  var selectTema = document.getElementById('tema');
  var inputTema = document.getElementById('tema_custom');
  if (selectTema && inputTema) {
    selectTema.addEventListener('change', function() {
      if (this.value) inputTema.value = this.value;
    });
    // Se o usuário digitar manualmente, limpa a seleção
    inputTema.addEventListener('input', function() {
      if (selectTema) selectTema.value = '';
    });
  }
});
