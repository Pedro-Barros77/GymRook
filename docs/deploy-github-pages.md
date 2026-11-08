# Publicar o piloto no GitHub Pages

O workflow `.github/workflows/pages.yml` já publica a pasta `dist/`, incluindo o piloto atual. Ele executa `npm run build` e `npm run check` com Node.js 22 e publica quando recebe um push na branch `main`, ou quando é iniciado manualmente. Não é necessário gerar as imagens novamente, instalar dependências npm, configurar secrets ou usar Python no deploy.

## Primeiro deploy

1. No GitHub, crie um repositório **público** chamado `GymRook`. Deixe desmarcadas as opções para adicionar README, `.gitignore` e licença: o repositório deve começar vazio. Repositórios públicos permitem usar Pages com GitHub Free.
2. Para uma pasta nova ainda sem repositório Git, abra o PowerShell e execute os comandos abaixo, substituindo `SEU_USUARIO` pelo seu usuário do GitHub. Se o projeto já está publicado, siga a seção Atualizações:

```powershell
Set-Location C:\Users\pedrao\source\repos\GymRook
git init -b main
git add .
git commit -m "Publica piloto do GymRook"
git remote add origin https://github.com/SEU_USUARIO/GymRook.git
git push -u origin main
```

Se o Git solicitar identificação no primeiro commit, configure `user.name` e `user.email` com os valores que você usa no GitHub. O push pode abrir a autenticação do GitHub.

3. No repositório, abra **Settings → Pages → Build and deployment → Source** e selecione **GitHub Actions**. O workflow já existe; não é preciso criar outro a partir de um template.
4. Abra **Actions → Publicar GymRook no GitHub Pages → Run workflow**, selecione `main` e confirme. Se a tentativa automática do primeiro push tiver falhado porque Pages ainda não estava habilitado, esta execução usa a configuração nova.
5. Aguarde o workflow terminar com sucesso. O endereço aparece no deploy e em **Settings → Pages → Visit site**. Para o nome sugerido, será:

```text
https://SEU_USUARIO.github.io/GymRook/
```

Só `dist/` entra no site publicado. Fontes e scripts ficam no repositório; `.cache/`, `output/` e `backups/` ficam fora do Git conforme `.gitignore`. Os backups locais continuam preservados. Há 31 exercícios com demonstrações distintas a 12 fps. O tamanho do pacote e a versão do cache ficam em `dist/asset-manifest.json`; o resultado da revisão está em [current-media-status.md](current-media-status.md).

## Testar no celular

Abra o endereço HTTPS, consulte os exercícios e reproduza as demonstrações. Na tela inicial, use **Baixar para usar offline** e aguarde a confirmação. Depois teste sem conexão. Para adicionar à tela inicial, use o menu de instalação do Chrome no Android ou Compartilhar → Adicionar à Tela de Início no Safari do iPhone.

## Atualizações

Após editar o projeto:

```powershell
git add .
git commit -m "Atualiza piloto"
git push
```

Cada push em `main` executa o workflow e publica `dist/` novamente. O build atualiza a versão do cache automaticamente. Se o celular ainda mostrar a versão antiga, feche todas as abas e a janela do app instalado e abra o guia novamente com conexão. Use novamente o download offline para confirmar a nova versão completa.

## Referências oficiais

- [Criar um site Pages e disponibilidade no GitHub Free](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Selecionar GitHub Actions como fonte de publicação](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Workflows de deploy do GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
