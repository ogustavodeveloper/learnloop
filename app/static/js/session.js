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
            location.reload()

        })
        .catch((error) => {
            Swal.fire('Erro', 'Não foi possível salvar o documento:' + error, 'error');
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

function gerarQuiz(session) {
    const formData = new FormData()
    const anotacao = document.getElementById("resumo").value.trim()
    const assunto = document.getElementById("assunto").textContent
    const arquivo = document.getElementById("quiz-file")?.files[0]

    const MAX_SIZE = 5 * 1024 * 1024
    const allowedTypes = ["application/pdf", "image/png", "image/jpg", "image/jpeg", "image/webp", "image/bmp", "image/gif"]

    if (!anotacao && !arquivo) {
        Swal.fire({title:'Atenção', text:'Envie uma anotação ou selecione um arquivo para gerar o quiz.', icon:'warning'});
        return;
    }
    if (anotacao && anotacao.length < 20 && !arquivo) {
        Swal.fire({title:'Atenção', text:'A anotação está muito curta. Escreva pelo menos 20 caracteres ou envie um arquivo.', icon:'warning'});
        return;
    }
    if (arquivo) {
        if (!allowedTypes.includes(arquivo.type)) {
            Swal.fire({title:'Atenção', text:'Formato de arquivo inválido. Use PDF ou imagem.', icon:'warning'});
            return;
        }
        if (arquivo.size > MAX_SIZE) {
            Swal.fire({title:'Atenção', text:'Arquivo muito grande. O limite é 5 MB.', icon:'warning'});
            return;
        }
        formData.append("arquivo_quiz", arquivo)
    }

    formData.append("sessao", session)
    formData.append("anotacao", anotacao)
    formData.append("assunto", assunto)

    let timerInterval;
    Swal.fire({
        title: "Quiz sendo criado!",
        html: "Aguarde alguns segundos, você vai ser direcionado automaticamente para o seu quiz exclusivo!",
        timer: 2000,
        timerProgressBar: true,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {
        /* Read more about handling dismissals below */
        if (result.dismiss === Swal.DismissReason.timer) {
            console.log("I was closed by the timer");
        }
    });
    axios.post("/api/gerar-quiz", formData).then(response => {
        if (response.data.msg == "success") {
            Swal.fire("Quiz Criado!", "Aproveite!", "success")
            window.location.href = `/quiz/${response.data.id}`
        } else {
            Swal.fire("Ocorreu um erro! Tente novamente.", `Detalhes do erro: ${response.data.details}`, "error")
        }
    })
}

function abrirModalArquivo(sessao) {
    Swal.fire({
        title: 'Selecione um arquivo',
        html: `<input type="file" id="swal-input-file" class="swal2-input" accept="*/*">`,
        showCancelButton: true,
        confirmButtonText: 'Enviar',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            const fileInput = Swal.getPopup().querySelector('#swal-input-file');
            if (!fileInput.files[0]) {
                Swal.showValidationMessage('Selecione um arquivo!');
                return false;
            }
            return fileInput.files[0];
        }
    }).then((result) => {
        if (result.isConfirmed && result.value) {
            const documento = result.value;
            const formData = new FormData();
            formData.append("documento", documento);
            formData.append("assunto", sessao);

            Swal.fire({
                title: 'Enviando arquivo...',
                html: 'Por favor, aguarde enquanto o arquivo é enviado.',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            axios.post('/add-doc', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
                .then(response => {
                    document.getElementById("documentos").innerHTML += `<a id="doc" href="${response.data.url} target="_blank">${response.data.filename}</a>`;
                    Swal.fire('Documento Salvo!', "Atualize a página!", 'success');
                })
                .catch((error) => {
                    Swal.fire('Erro', 'Não foi possível salvar o documento: ' + error, 'error');
                });
        }
    });
}

function deletarDoc(id, btn) {
    if (confirm("Tem certeza que deseja deletar este documento?")) {
        fetch(`/api/delete-doc/${id}`, { method: "POST" })
            .then(r => r.json())
            .then(d => {
                if (d.msg === "success") {
                    btn.parentElement.remove();
                } else {
                    alert("Erro ao deletar documento.");
                }
            });
    }
}