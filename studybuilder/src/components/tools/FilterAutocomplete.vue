<template>
<v-slide-item>
  <v-menu
    :close-on-content-click="false"
    v-if="isDate(item.value)"
  >
    <template v-slot:activator="{ on, attrs }">
      <v-text-field
        :label="data.length === 0 ? item.text : (data.length === 1 ? data[0] : `${data[0]} - ${data[1]}`)"
        append-icon="mdi-calendar"
        readonly
        rounded
        class="mt-1 calendar filterAutocompleteLabel"
        v-bind="attrs"
        v-on="on">
      </v-text-field>
    </template>
    <v-date-picker
      type="date"
      range
      v-model="data"
      @input="filterDate()"
      v-show="!monthPicker"
      :selected-items-text="$t('FilterAutocomplete.range_selected')"
    >
    <v-btn
      text
      color="primary"
      @click="clear()">
        {{$t('FilterAutocomplete.clear')}}
    </v-btn>
    <v-btn
      text
      color="primary"
      @click="switchCalendar()">
        {{$t('FilterAutocomplete.month_picker')}}
    </v-btn>
    </v-date-picker>
    <v-date-picker
      type="month"
      range
      v-model="data"
      @input="filterDate()"
      v-show="monthPicker"
      :selected-items-text="$t('FilterAutocomplete.range_selected')"
    >
    <v-btn
      text
      color="primary"
      @click="clear()">
        {{$t('FilterAutocomplete.clear')}}
    </v-btn>
    <v-btn
      text
      color="primary"
      @click="switchCalendar()">
        {{$t('FilterAutocomplete.day_picker')}}
    </v-btn>
    </v-date-picker>
  </v-menu>
  <v-select
    ref="select"
    v-else
    dense
    clearable
    multiple
    rounded
    no-filter
    :label="item.text"
    font-weight-black
    v-model="data"
    v-bind:class="isEmpty(item.value) ? 'autocomplete empty fixed-width' : 'autocomplete full fixed-width'"
    :items="items"
    @input="getColumnData(item.value)"
    @change="filterTable()"
    class="mt-4 select filterAutocompleteLabel"
    >
    <template v-slot:prepend-item>
      <v-row>
        <v-text-field
          class="pl-6"
          v-model="searchString"
          :placeholder="$t('FilterAutocomplete.search')"
          @input="getColumnData(item.value)">
        </v-text-field>
        <v-btn
          fab
          small
          icon
          class="mr-3 mt-2"
          @click="close()"
          >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-row>
    </template>
    <template v-slot:selection="{index}">
      <div v-if="index === 0">
        <span class="items-font-size">{{ data[0].substring(0, 12) + '...' }}</span>
      </div>
      <span
        v-if="index === 1"
        class="grey--text text-caption mr-1"
      >
        (+{{ data.length -1 }})
      </span>
    </template>
  </v-select>
</v-slide-item>
</template>

<script>
import columnData from '@/api/columnData'

export default {
  props: {
    item: Object,
    clearInput: Number,
    conditional: {
      type: Boolean,
      default: false
    },
    filters: String,
    trigger: {
      type: Number,
      default: 0
    },
    resource: Array,
    library: String,
    parameters: Object,
    filtersModifyFunction: {
      type: Function,
      required: false
    },
    initialData: {
      type: Array,
      required: false
    }
  },
  data () {
    return {
      data: [],
      items: [],
      searchString: '',
      name: '',
      monthPicker: false
    }
  },
  created () {
    if (!this.initialData) {
      this.getColumnData(this.item.value)
    } else {
      this.items = [...this.initialData]
    }
  },
  methods: {
    getWidth (item) {
      return 'width: ' + (item.length * 10).toString() + 'px'
    },
    close () {
      this.searchString = ''
      this.$refs.select.blur()
    },
    switchCalendar () {
      this.monthPicker = !this.monthPicker
    },
    clear () {
      this.data = []
      this.filterTable()
    },
    isDate () {
      if (Date.parse(new Date(this.items[0])) && this.items[0].length > 20) {
        return true
      } else {
        return false
      }
    },
    isEmpty () {
      if (this.data.length > 0) {
        return false
      }
      return true
    },
    getColumnData (value) {
      if (value === 'actions') {
        return []
      }
      let jsonFilter = JSON.parse(this.filters)
      delete jsonFilter[value]
      let params = {
        fieldName: (this.item.externalFilterSource ? this.item.externalFilterSource.substring(this.item.externalFilterSource.indexOf('$') + 1) : (this.item.filteringName ? this.item.filteringName : value)),
        searchString: this.searchString,
        resultCount: 10
      }
      if (this.parameters) {
        params = Object.assign(params, this.parameters)
      }
      if (this.filtersModifyFunction) {
        const filters = this.filtersModifyFunction(jsonFilter, params)
        jsonFilter = filters.jsonFilter
        params = filters.params
      }
      if (!this.item.externalFilterSource) {
        params.filters = jsonFilter
      }
      if (this.resource[1] !== undefined) {
        params.codelist_uid = this.resource[1]
      }
      if (this.library) {
        params.library = this.library
      }
      if (this.item.externalFilterSource) {
        this.resource[0] = this.item.externalFilterSource.substring(0, this.item.externalFilterSource.indexOf('$'))
      }
      columnData.getHeaderData(params, this.resource[0]).then(resp => {
        this.items = this.booleanValidator(resp.data)
        this.items = this.items.filter(element => {
          return element !== ''
        })
        if (typeof (this.items[0]) === 'object') {
          const deconstructedItems = []
          this.items.forEach(item => {
            if (item.length > 1) {
              item.forEach(i => {
                deconstructedItems.push(i.name)
              })
            } else if (item.length !== 0) {
              deconstructedItems.push(item[0].name)
            }
          })
          this.items = Array.from(new Set(deconstructedItems))
        }
        this.data.forEach(element => {
          this.items.push(element)
        })
        if (this.initialData) {
          this.items = this.items.filter(item => this.initialData.indexOf(item) !== -1)
        }
      })
    },
    filterDate () {
      let dateData = []
      if (this.data[0].length === 7) {
        if (this.data.length === 1) {
          dateData = [this.data[0] + '-01', this.getSecondDay(this.data[0], 30)]
        } else {
          dateData = [this.data[0] + '-01', this.getSecondDay(this.data[1], 30)]
        }
      } else {
        if (this.data.length === 1) {
          dateData = [this.data[0], this.getSecondDay(this.data[0], 1)]
        } else {
          dateData = [this.data[0], this.getSecondDay(this.data[1], 1)]
        }
      }
      this.$emit('filter', { column: this.item.value, data: dateData })
    },
    booleanConverter (value) {
      if (value === 'No' || value === false) {
        return value === 'No' ? false : 'No'
      } else {
        return value === 'Yes' ? true : 'Yes'
      }
    },
    booleanValidator (array) {
      if (array.length <= 2 && (array[0] === false || array[0] === true)) {
        array.forEach(el => {
          const index = array.indexOf(el)
          array[index] = this.booleanConverter(array[index])
        })
      }
      return array
    },
    filterTable () {
      if (this.data.length <= 2 && (this.data[0] === 'Yes' || this.data[0] === 'No')) {
        const requestData = []
        this.data.forEach(el => {
          const index = this.data.indexOf(el)
          requestData.push(this.booleanConverter(this.data[index]))
        })
        this.$emit('filter', { column: this.item.filteringName ? this.item.filteringName : this.item.value, data: requestData })
      } else {
        this.$emit('filter', { column: this.item.filteringName ? this.item.filteringName : this.item.value, data: this.data })
      }
    },
    getSecondDay (day, days) {
      const date = new Date(Date.parse(day))
      return new Date(date.setDate(date.getDate() + days)).toISOString().split('T')[0]
    }
  },
  watch: {
    searchString: function () {
      this.getColumnData(this.item.value)
    },
    clearInput: function () {
      this.clear()
    },
    trigger: function () {
      this.getColumnData(this.item.value)
    }
  }
}
</script>
<style scoped>
.v-list {
  max-width: 300px;
}
.select {
  width: 300px;
}
.fixed-width {
  max-width: 250px;
}
.items-font-size {
  font-size: 14px;
}
</style>
