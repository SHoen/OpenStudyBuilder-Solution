<template>
<v-card color="greyBackground">
  <v-card-title>
    <span class="headline">{{ $t('Settings.title') }}</span>
    <help-button-with-panels :title="$t('_global.help')" :items="helpItems" />
  </v-card-title>
  <v-card-text>
    <div class="white pa-4">
      <v-switch
        v-model="form.darkTheme"
        :label="$t('Settings.toggle')"
        class="mt-4"
        @change="toggleDarkTheme()"
        />
      <v-select
        v-model="form.rows"
        :label="$t('Settings.rows')"
        :items="rows"
        item-text="name"
        item-value="value"
        clearable
        ></v-select>
      <v-text-field
        v-model="form.studyNumberLength"
        :label="$t('Settings.study_number_length')"
        type="number"
        clearable
        />
      <v-switch
        v-model="form.multilingual"
        :label="$t('Settings.multilingual_crf')"
        data-cy="settings-multilingual-crf"
        class="mt-4"
        />
    </div>
  </v-card-text>
  <v-card-actions class="pb-4">
    <v-spacer />
    <v-btn
      class="secondary-btn"
      color="white"
      @click="close"
      >
      {{ $t('_global.cancel') }}
    </v-btn>
    <v-btn
      color="secondary"
      data-cy="save-settings-button"
      @click="save"
      :loading="working"
      >
      {{ $t('_global.save') }}
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import { mapGetters } from 'vuex'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'

export default {
  components: {
    HelpButtonWithPanels
  },
  computed: {
    ...mapGetters({
      userData: 'app/userData'
    })
  },
  data () {
    return {
      darkTheme: localStorage.getItem('userData.darkTheme') || false,
      helpItems: [
        'Settings.rows',
        'Settings.study_number_length'
      ],
      rows: [{
        value: 5,
        name: '5'
      }, {
        value: 10,
        name: '10'
      }, {
        value: 15,
        name: '15'
      }, {
        value: 0,
        name: this.$t('_global.all')
      }],
      title: this.$t('Settings.title'),
      form: {},
      working: false
    }
  },
  methods: {
    close () {
      this.$emit('close')
    },
    save () {
      this.working = true
      this.$store.commit('app/SET_USER_DATA', this.form)
      this.close()
      this.working = false
    },
    toggleDarkTheme () {
      this.$vuetify.theme.dark = !this.$vuetify.theme.dark
    }
  },
  watch: {
    userData: {
      handler: function (val) {
        this.form = JSON.parse(JSON.stringify(val))
      },
      immediate: true
    }
  }
}
</script>
