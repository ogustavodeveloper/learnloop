function redacao() {
  var title = document.getElementById("titulo");
  var conteudo = document.getElementById("conteudo");

  Swal.fire({
    title: "Corrigindo sua redação...",
    text: "Aguarde, em instantes você será redirecionado para uma página com a correção detalhada.",
    icon: "info"
  })
  
  axios.post("/learn-ai/redacao", {
    title: title.value,
    content: conteudo.value,
    nivel: document.getElementById("nivel").value,
    tema: document.getElementById("tema").value
  }).then((r) => {
    if (r.data.msg === "success") {
      window.location.href = '/correcao/'+r.data.response
    } else {
      Swal.fire({
        title: "Erro ao corrigir sua redação",
        text: `Tire um print da mensagem ao lado e mande para o Instagram do Estudaê (@estudae.of) para podermos resolver este erro: ${r.data.details}`,
        icon: 'error'
      })
    }
  }).catch((error) => {
    Swal.fire({
      title: "Houve um erro ao corrigir a sua redacão.",
      text: `Tire um print da mensagem ao lado e mande para o Instagram do Estudaê (@estudae.of) para podermos resolver este erro: ${error}`,
      icon: "error"
    })
    console.error("Erro:", error);
  });
}

Swal.fire({
  title: "Conheça o Corretor de Redação",
  text: "Envie sua redação para receber orientações do Learn.Ai, a inteligência artificial do Estudaê. Você pode digitar ou enviar uma foto da redação manuscrita. Se quiser, pode salvar a redação na sua conta, mas isso é opcional. Não se preocupe, sua redação só será armazenada se você optar por isso. Estamos aqui para ajudar você a se preparar para o ENEM. 💡",
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
  var tema = document.getElementById("tema").value;
  var texto = document.getElementById("conteudo").value;

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
    texto: texto
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
}
