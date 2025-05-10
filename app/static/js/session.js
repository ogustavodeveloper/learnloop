function sendArquivo(sessao) {
    const documento = document.getElementById("documento-novo").files[0];
    const assunto = sessao

    const formData = new FormData();
    formData.append("documento", documento)
    formData.append("assunto", assunto)

    axios.post('/add-doc', formData, {
                                headers: {
                                                                  'Content-Type': 'multipart/form-data'
                                                                                                            }
                                                                                                                                                            
                                                                                                                                                                        })
                                                                                                                                                                                        .then(response => {
                                                                                                                                                                                                            Swal.fire('Documento Salvo!', "Atualize a página !", 'success');
                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                })
                                                                                                                                                                                                                                                                .catch((error) => {
                                                                                                                                                                                                                                                                                    Swal.fire('Erro', 'Não foi possível salvar o documento:' + error , 'error');
                                                                                                                                                                                                                                                                                                    });


    }

function updateAnotacao(sessao) {
    const anotacao = document.getElementById("resumo").value

    const formData = new FormData()
    formData.append("anotacao", anotacao)
    formData.append("sessao", sessao)

    axios.post("/update-anotacao", formData).then(response => {
        Swal.fire("Anotação Atualizada com sucesso!", "Muito bem, continue estudando!", "success")
    })
}