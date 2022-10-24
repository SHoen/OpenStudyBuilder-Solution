<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  @close="close"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <v-data-table
      :headers="choosenItemsheaders"
      :items="choosenItems"
      >
      <template v-slot:item.delete="{ item }">
        <v-btn
          icon
          class="mt-1 rightButtons"
          @click="removeItem(item)"
          data-cy="remove-item-link">
          <v-icon dark>
              mdi-trash-can
          </v-icon>
        </v-btn>
      </template>
    </v-data-table>
    <v-col class="pt-0 mt-0">
      <n-n-table
        :headers="availableItemsHeaders"
        item-key="uid"
        :items="items"
        has-api
        :options.sync="options"
        :server-items-length="total"
        @filter="fetchActivities"
        hide-export-button
        hide-default-switches
        additional-margin
        data-cy="test">
          <template v-slot:item.add="{ item }">
            <v-btn
              icon
              class="mt-1 rightButtons"
              data-cy="add-item-link"
              @click="addItem(item)">
              <v-icon dark>
                  mdi-plus
              </v-icon>
            </v-btn>
          </template>
      </n-n-table>
    </v-col>
  </template>
</simple-form-dialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import crfs from '@/api/crfs'
import NNTable from '@/components/tools/NNTable'
import activities from '@/api/activities'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    SimpleFormDialog,
    NNTable
  },
  props: {
    itemToLink: Object,
    itemType: String,
    open: Boolean
  },
  computed: {
    title () {
      return this.itemType === 'form' ? this.$t('CrfLinikingForm.link_activity_groups') : (this.itemType === 'itemGroup' ? this.$t('CrfLinikingForm.link_activity_sub_groups') : this.$t('CrfLinikingForm.link_activities'))
    }
  },
  data () {
    return {
      helpItems: [],
      items: [],
      choosenItems: [],
      choosenItemsheaders: [
        { text: this.$t('_global.name'), value: 'name' },
        { text: '', value: 'delete' }
      ],
      availableItemsHeaders: [
        { text: this.$t('_global.name'), value: 'name' },
        { text: '', value: 'add' }
      ],
      total: 0,
      options: {}
    }
  },
  methods: {
    submit () {
      const data = []
      this.choosenItems.forEach(el => {
        data.push({ uid: el.uid })
      })
      if (this.itemType === 'form') {
        crfs.addActivityGroupsToForm(data, this.itemToLink.uid).then(resp => {
          this.close()
        })
      } else if (this.itemType === 'itemGroup') {
        crfs.addActivitySubGroupsToItemGroup(data, this.itemToLink.uid).then(resp => {
          this.close()
        })
      } else {
        crfs.addActivitiesToItem(data, this.itemToLink.uid).then(resp => {
          this.close()
        })
      }
    },
    addItem (item) {
      if (!this.choosenItems.some(el => el.uid === item.uid)) {
        this.choosenItems.push(item)
      }
    },
    removeItem (item) {
      this.choosenItems = this.choosenItems.filter(el => el.uid !== item.uid)
    },
    close () {
      this.choosenItems = []
      this.items = []
      this.$emit('close')
    },
    fetchActivities (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      if (this.itemType === 'form') {
        activities.getAllGroups(params).then(resp => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      } else if (this.itemType === 'itemGroup') {
        activities.getAllSubGroups(params).then(resp => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      } else {
        activities.get(params, 'activities').then(resp => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      }
    }
  },
  mounted () {
    this.fetchActivities()
    this.choosenItems = this.itemToLink ? (this.itemToLink.activityGroups || this.itemToLink.activitySubGroups || this.itemToLink.activities) : []
  },
  watch: {
    itemToLink (value) {
      if (value) {
        this.fetchActivities()
        this.choosenItems = this.itemToLink.activityGroups || this.itemToLink.activitySubGroups || this.itemToLink.activities
      }
    },
    options () {
      this.fetchActivities()
    }
  }
}
</script>
<style scoped>
  .rightButtons {
    float: right;
  }
</style>
