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
      document.getElementById("resposta").innerHTML = r.data.details;
    }
  }).catch((error) => {
    document.getElementById("resposta").innerHTML = "Houve um erro ao corrigir sua redação, tente novamente! Se o erro persistir, entre em contato pelo nosso Instagram: @learnloop.of e informe que deu erro ao corrigir sua redação que vamos te dar todo o suporte necessário e o mais rápido possível!";
    console.error("Erro:", error);
  });
}

Swal.fire({
  title: "Conheça o Corretor de Redação",
  text: "Envie sua redação para receber orientações do Learn.Ai, a inteligência artificial do LearnLoop. Você pode digitar ou enviar uma foto da redação manuscrita. Se quiser, pode salvar a redação na sua conta, mas isso é opcional. Não se preocupe, sua redação só será armazenada se você optar por isso. Estamos aqui para ajudar você a se preparar para o ENEM. 💡",
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
        console.error("Erro ao carregar a foto:", error);
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
