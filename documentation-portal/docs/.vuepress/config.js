module.exports = {
    base: '/doc/',
    title: 'StudyBuilder Documentation Portal',
    description: 'The scope and purpose of the StudyBuilder is to support the clinical study process from planning, study design, study specification, study set-up to drive downstream automation',
    themeConfig: {
        logo: '/NN-logo-whitebackground.png',
        // docsDir: '',
        lastUpdated: 'Last Updated', // string | boolean
        nav: [
            { text: 'Home', link: '/' },
            //{ text: 'Guide', link: '/guides/' }
        ],
        sidebar: {
            '/guides/': [
                '',
                {
                    title: 'User Guides',
                    collapsable: true,
                    children: [
                        'userguide/userguides_introduction'
                    ]
                },
                {
                    title: 'Solution Architecture',
                    collapsable: true,
                    children: [
                        'architecture/architecture_introduction',
						'architecture/conceptual_architecture',
						'architecture/system_component_architecture',
						'architecture/integration_architecture',
                        'architecture/system_data_flows',
						'architecture/cloud_architecture',
						'architecture/application_architecture_api',
						'architecture/mdr_api_architecture',
						'architecture/mdr_data_architecture',
						'architecture/authentication_authorisation_architecture'
                    ]
                }
            ],
            '/': [ // Your fallback (this is your landing page)
                '' // this is your README.md (main)
            ]
        }
    },
    chainWebpack: (config, isServer) => {
        config.module.rule('vue').uses.store.get('vue-loader').store.get('options').transformAssetUrls = {
            video: ['src', 'poster'],
            source: 'src',
            img: 'src',
            image: ['xlink:href', 'href'],
            a: 'href'
        }
    }
}
