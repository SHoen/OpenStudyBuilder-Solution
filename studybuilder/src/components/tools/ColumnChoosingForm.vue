<template>
<v-card>

  <v-card-title class="pt-6 pb-0">
    <span class="headline">
      {{ title }}
    </span>
  </v-card-title>

  <v-card-text>
    <v-container>
      <v-row>
        <v-col
          cols="12"
          class="pl-0"
        >
          <v-text-field
            v-model="search"
            :label="$t('ColumnChoosingForm.filtersSearch')"
            hide-details
            class="mb-3"/>
          <v-switch
            v-for="item in filteredList"
            :label="item.text"
            :key="item.value"
            :value="item"
            data-cy="toggle-button"
            v-model="displayedColumns">
          </v-switch>
        </v-col>
      </v-row>
    </v-container>
  </v-card-text>
  <v-card-actions class="pb-6">
    <v-btn
      color="primary"
      @click="restoreDefaultsAndSave"
    >
      {{ restoreLabel }}
    </v-btn>
    <v-spacer />
    <v-btn
      class="secondary-btn"
      color="white"
      @click="cancel"
    >
      {{$t('_global.cancel')}}
    </v-btn>
    <v-btn
      color="secondary"
      @click="save"
    >
      {{$t('_global.apply')}}
    </v-btn>
  </v-card-actions>

</v-card>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  components: {
  },
  props: {
    availableColumns: Array,
    tableName: String,
    title: String,
    restoreLabel: String,
    filtering: {
      type: Boolean,
      default: false
    },
    alreadyInFilter: Array
  },
  data () {
    return {
      displayedColumns: [],
      search: '',
      initialData: []
    }
  },
  computed: {
    filteredList () {
      return this.availableColumns.filter(column => {
        return column.text.toLowerCase().includes(this.search.toLowerCase()) && column.text !== ''
      })
    },
    ...mapGetters({
      columns: 'tablesLayout/columns'
    })
  },
  mounted () {
    this.initialData = this.displayedColumns = this.columns[this.tableName]
    if (this.isFiltering()) {
      this.initialData = this.displayedColumns = this.alreadyInFilter
    } else if (!this.initialData || this.initialData.length === 0) {
      this.initialData = this.displayedColumns = this.availableColumns
    }
  },
  methods: {
    restoreDefaultsAndSave () {
      this.displayedColumns = this.isFiltering() ? [] : this.availableColumns
      this.$emit('clear')
      this.save()
    },
    save () {
      const check = new Set()
      this.displayedColumns = this.displayedColumns.filter(obj => !check.has(obj.value) && check.add(obj.value))
      const actionsIndex = this.displayedColumns.findIndex(i => i.text === '')
      if (actionsIndex !== -1) {
        this.displayedColumns.unshift(this.displayedColumns.splice(actionsIndex, 1)[0])
      }
      this.$emit('save', this.displayedColumns)
      if (this.tableName !== '') {
        const layoutMap = new Map()
        layoutMap.set(this.tableName, this.displayedColumns)
        this.$store.commit('tablesLayout/SET_COLUMNS', layoutMap)
        this.initialData = this.displayedColumns
      }
      this.close()
    },
    close () {
      this.search = ''
      this.$emit('close')
    },
    cancel () {
      this.displayedColumns = this.isFiltering() ? this.alreadyInFilter : this.initialData
      this.close()
    },
    isFiltering () {
      return this.filtering
    }
  }
}
</script>
