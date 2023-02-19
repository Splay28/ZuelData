$(function() {
    tinymce.init({
        //选择class为content的标签作为编辑器
        selector: '#rich_content',
        automatic_uploads: false,
        images_upload_url: '/api/upload/blogpic',
        //plugins: 'clearhtml searchreplace layout image  link media code codesample table charmap hr pagebreak nonbreaking lists help emoticons autosave bdmap indent2em lineheight formatpainter axupimgs letterspacing  quickbars wordcount',
        plugins: 'fullscreen preview searchreplace image searchreplace layout indent2em link code table charmap hr pagebreak nonbreaking lists help lineheight formatpainter axupimgs letterspacing  quickbars wordcount',
        font_size_formats: '12px 14px 16px 18px 24px 36px 48px 56px 72px',
        font_family_formats: '微软雅黑=Microsoft YaHei,Helvetica Neue,PingFang SC,sans-serif;苹果苹方=PingFang SC,Microsoft YaHei,sans-serif;宋体=simsun,serif;仿宋体=FangSong,serif;黑体=SimHei,sans-serif;',

        toolbar: 'code forecolor backcolor bold italic underline strikethrough link indent2em outdent indent lineheight letterspacing bullist numlist blockquote subscript superscript layout removeformat table image media upfile charmap hr pagebreak styles fontfamily fontsize cut copy undo redo restoredraft searchreplace fullscreen help',
        
        //toolbar: 'undo redo | styles | bold italic | link image code | alignleft aligncenter alignright alignjustify | indent outdent',
        //方向从左到右
        directionality: 'ltr',
        paste_data_images: true,
        toolbar_sticky: false,
        //语言选择中文
        language: 'zh_CN',
        //高度为400
        height: 400,
        width: '100%',
        
        images_upload_url_base: '/api/upload',
        placeholder: '在这里输入博客的正文...',
        //按tab不换行
        nonbreaking_force_tab: true,
        branding: false,
        menubar: false
    });
})