<template>
<div>
  <n-n-table
    :headers="returnHeaders()"
    :items="activities"
    export-object-label="Activities"
    :export-data-url="`concepts/activities/${source}`"
    item-key="uid"
    :server-items-length="total"
    :options.sync="options"
    has-api
    @filter="fetchActivities"
    :column-data-resource="`concepts/activities/${source}`"
    @item-expanded="getSubGroups"
    :show-expand="isExpand()"
    :subTables="isExpand()"
    has-history
    single-expand
    :filters-modify-function="modifyFilters"
    >
    <template v-slot:item="{ item, expand, isExpanded }" v-if="isExpand()">
      <tr style="background-color: lightskyblue">
        <td width="5%">
          <v-btn @click="expand(!isExpanded)" v-if="isExpanded" icon>
            <v-icon dark>
              mdi-chevron-up
            </v-icon>
          </v-btn>
          <v-btn @click="expand(!isExpanded)" v-else icon>
            <v-icon dark>
              mdi-chevron-down
            </v-icon>
          </v-btn>
        </td>
        <td width="5%">
          <actions-menu :actions="actions" :item="item"/>
        </td>
        <td width="41%" :class="'font-weight-bold'">{{ item.name }}</td>
        <td width="24%">{{ item.startDate | date }}</td>
        <td width="14%"><status-chip :status="item.status" /></td>
        <td width="10%">{{ item.version }}</td>
      </tr>
    </template>
    <template v-slot:item.possibleActions="{ item }">
      <div class="pr-0 mr-0">
        <actions-menu :actions="actions" :item="item"/>
      </div>
    </template>
    <template v-slot:item.name="{ item }">
      <div :class="isExpand() ? 'font-weight-bold' : ''"> {{ item.name }} </div>
    </template>
    <template v-slot:item.status="{ item }">
      <status-chip :status="item.status" />
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate | date }}
    </template>
    <template v-slot:item.activityGroups="{ item }">
      {{ groupsDisplay(item) }}
    </template>
    <template v-slot:item.activitySubGroups="{ item }">
      {{ subGroupsDisplay(item) }}
    </template>
    <template v-slot:item.activities="{ item }">
      {{ activitiesDisplay(item) }}
    </template>
    <template v-slot:expanded-item="{ headers }">
      <td :colspan="headers.length" class="pa-0">
        <v-data-table
          class="elevation-0"
          :headers="groupsHeaders"
          :items="subgroups"
          item-key="uid"
          hide-default-footer
          hide-default-header
          light
          :loading="loading"
          :show-expand="true"
          @item-expanded="getSubgroupActivities"
          single-expand
          >
          <template v-slot:item="{ item, expand, isExpanded }">
            <tr>
              <td width="5%">
                <v-btn @click="expand(!isExpanded)" v-if="isExpanded" icon>
                  <v-icon dark>
                    mdi-chevron-up
                  </v-icon>
                </v-btn>
                <v-btn @click="expand(!isExpanded)" v-else icon>
                  <v-icon dark>
                    mdi-chevron-down
                  </v-icon>
                </v-btn>
              </td>
              <td width="5%">
                <actions-menu :actions="actions" :item="item" :source="'activity-sub-groups'"/>
              </td>
              <td width="41%" class="font-weight-bold">{{ item.name }}</td>
              <td width="24%">{{ item.startDate | date }}</td>
              <td width="14%"><status-chip :status="item.status" /></td>
              <td width="10%">{{ item.version }}</td>
            </tr>
          </template>
          <template v-slot:expanded-item="{ headers }">
            <td :colspan="headers.length" class="pa-0">
              <v-data-table
                class="elevation-0"
                :headers="groupsHeaders"
                :items="subgroupActivities"
                item-key="uid"
                hide-default-footer
                hide-default-header
                light
                :loading="subLoading"
                :show-expand="true"
                >
                <template v-slot:item="{ item }">
                  <tr>
                    <td width="5%">&nbsp;</td>
                    <td width="5%">
                      <actions-menu :actions="actions" :item="item" :source="'activities'"/>
                    </td>
                    <td width="41%">{{ item.name }}</td>
                    <td width="24%">{{ item.startDate | date }}</td>
                    <td width="14%"><status-chip :status="item.status" /></td>
                    <td width="10%">{{ item.version }}</td>
                  </tr>
                </template>
              </v-data-table>
            </td>
          </template>
        </v-data-table>
      </td>
    </template>
    <template v-slot:actions="">
      <slot name="extraActions"></slot>
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="showForm"
        :title="$t('CodelistCreationForm.title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
  </n-n-table>
  <activities-form
    :open="showActivityForm"
    @close="closeForm"
    :edited-activity="activeActivity"/>
  <v-dialog
      v-model="showGroupsForm"
      persistent
      max-width="800px"
      content-class="top-dialog"
    >
    <activities-groups-form
      @close="closeForm"
      :edited-activity="activeActivity"/>
  </v-dialog>
  <v-dialog
      v-model="showInstantiationsForm"
      persistent
      max-width="800px"
      content-class="top-dialog"
    >
    <activities-instantiations-form
      @close="closeForm"
      :edited-activity="activeActivity"/>
  </v-dialog>
</div>
</template>

<script>
import activities from '@/api/activities'
import ActionsMenu from '@/components/tools/ActionsMenu'
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'
import ActivitiesForm from '@/components/library/ActivitiesForm'
import ActivitiesGroupsForm from '@/components/library/ActivitiesGroupsForm'
import ActivitiesInstantiationsForm from '@/components/library/ActivitiesInstantiationsForm'

export default {
  components: {
    ActionsMenu,
    NNTable,
    StatusChip,
    ActivitiesForm,
    ActivitiesGroupsForm,
    ActivitiesInstantiationsForm
  },
  props: {
    source: String
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.possibleActions.find(action => action === 'approve'),
          click: this.approveActivity
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit'),
          click: this.editActivity
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'newVersion'),
          click: this.newActivityVersion
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'inactivate'),
          click: this.inactivateActivity
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'reactivate'),
          click: this.reactivateActivity
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.deleteActivity
        }
      ],
      activities: [],
      activitiesHeaders: [
        { text: '', value: 'possibleActions', width: '5%' },
        { text: this.$t('ActivityTable.activity_group'), value: 'activityGroup.name', externalFilterSource: 'concepts/activities/activity-groups$name' },
        { text: this.$t('ActivityTable.activity_subgroup'), value: 'activitySubGroup.name', externalFilterSource: 'concepts/activities/activity-sub-groups$name' },
        { text: this.$t('ActivityTable.activity'), value: 'name', externalFilterSource: 'concepts/activities/activities$name' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      instantiationsHeaders: [
        { text: '', value: 'possibleActions', width: '5%' },
        { text: this.$t('_global.library'), value: 'libraryName' },
        { text: this.$t('ActivityTable.type'), value: 'type' },
        { text: this.$t('ActivityTable.activity'), value: 'activities', externalFilterSource: 'concepts/activities/activities$name' },
        { text: this.$t('ActivityTable.instance'), value: 'name' },
        { text: this.$t('_global.definition'), value: 'definition' },
        { text: this.$t('ActivityTable.topic_code'), value: 'topicCode' },
        { text: this.$t('ActivityTable.adam_code'), value: 'adamParamCode' },
        { text: this.$t('ActivityTable.sdtm_domain'), value: 'sdtmDomain.name' },
        { text: this.$t('ActivityTable.sdtm_variable'), value: 'sdtmVariable.name' },
        { text: this.$t('ActivityTable.sdtm_category'), value: 'sdtmCat.name' },
        { text: this.$t('ActivityTable.sdtm_sub_category'), value: 'sdtmSubcat.name' },
        { text: this.$t('ActivityTable.specimen'), value: 'specimen.name' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'userInitials' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      groupsHeaders: [
        { text: '', value: 'possibleActions', width: '5%' },
        { text: this.$t('ActivityTable.group_or_subgroup'), value: 'name', width: '43%' },
        { text: this.$t('_global.modified'), value: 'startDate', width: '25%' },
        { text: this.$t('_global.status'), value: 'status', width: '15%' },
        { text: this.$t('_global.version'), value: 'version', width: '10%' }
      ],
      total: 0,
      options: {},
      filters: '',
      subgroups: [],
      currentGroup: '',
      currentSubGroup: '',
      showActivityForm: false,
      showGroupsForm: false,
      showInstantiationsForm: false,
      activeActivity: null,
      loading: false,
      subLoading: false,
      subgroupActivities: []
    }
  },
  methods: {
    fetchActivities (filters, sort, filtersUpdated) {
      if (filtersUpdated) {
        /* Filters changed, reset page number */
        this.options.page = 1
      }
      if (filters !== undefined) {
        this.filters = filters
      }
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      if (this.filters && this.filters !== undefined && this.filters !== '{}' && this.source === 'activities') {
        const filtersObj = JSON.parse(this.filters)
        if (filtersObj.activityGroups) {
          params.activityGroupNames = []
          filtersObj.activityGroups.v.forEach(value => {
            params.activityGroupNames.push(value)
          })
          delete filtersObj.activityGroups
        }
        if (filtersObj.activitySubGroups) {
          params.activitySubGroupNames = []
          filtersObj.activitySubGroups.v.forEach(value => {
            params.activitySubGroupNames.push(value)
          })
          delete filtersObj.activitySubGroups
        }
        if (filtersObj.name) {
          params.activityNames = []
          filtersObj.name.v.forEach(value => {
            params.activityNames.push(value)
          })
          delete filtersObj.name
        }
        if (Object.keys(filtersObj).length !== 0 && filtersObj.constructor === Object) {
          params.filters = JSON.stringify(filtersObj)
        }
      } else if (this.filters && this.filters !== undefined && this.filters !== '{}' && this.source === 'activity-instances') {
        const filtersObj = JSON.parse(this.filters)
        if (filtersObj.activities) {
          params.activityNames = []
          filtersObj.activities.v.forEach(value => {
            params.activityNames.push(value)
          })
          delete filtersObj.activities
        }
        if (filtersObj.specimen) {
          params.specimenNames = []
          filtersObj.specimen.v.forEach(value => {
            params.specimenNames.push(value)
          })
          delete filtersObj.specimen
        }
        if (Object.keys(filtersObj).length !== 0 && filtersObj.constructor === Object) {
          params.filters = JSON.stringify(filtersObj)
        }
      } else if (filters !== undefined && filters !== '{}') {
        params.filters = filters
      }
      if (this.options.sortBy.length !== 0 && sort !== undefined) {
        params.sortBy = `{"${this.options.sortBy[0]}":${!sort}}`
      }
      activities.get(params, this.source).then(resp => {
        this.activities = resp.data.items
        this.total = resp.data.total
      })
      activities.getSubGroups(this.currentGroup).then(resp => {
        this.subgroups = resp.data.items
      })
      activities.getSubGroupActivities(this.currentSubGroup).then(resp => {
        this.subgroupActivities = resp.data.items
      })
    },
    modifyFilters (jsonFilter, params) {
      if (jsonFilter.activityGroups) {
        params.activityGroupNames = []
        jsonFilter.activityGroups.v.forEach(value => {
          params.activityGroupNames.push(value)
        })
        delete jsonFilter.activityGroups
      }
      if (jsonFilter.activitySubGroups) {
        params.activitySubGroupNames = []
        jsonFilter.activitySubGroups.v.forEach(value => {
          params.activitySubGroupNames.push(value)
        })
        delete jsonFilter.activitySubGroups
      }
      if (jsonFilter.name) {
        params.activityNames = []
        jsonFilter.name.v.forEach(value => {
          params.activityNames.push(value)
        })
        delete jsonFilter.name
      }
      if (jsonFilter.activities) {
        params.activityNames = []
        jsonFilter.activities.v.forEach(value => {
          params.activityNames.push(value)
        })
        delete jsonFilter.activities
      }
      if (jsonFilter.specimen) {
        params.specimenNames = []
        jsonFilter.activities.v.forEach(value => {
          params.specimenNames.push(value)
        })
        delete jsonFilter.specimen
      }
      const filters = {
        jsonFilter: jsonFilter,
        params: params
      }
      return filters
    },
    isExpand () {
      return this.source === 'activity-groups'
    },
    subGroupsDisplay (item) {
      let display = ''
      item.activitySubGroups.forEach(element => {
        display += element.name + ', '
      })
      return display.slice(0, -2)
    },
    groupsDisplay (item) {
      let display = ''
      item.activityGroups.forEach(element => {
        display += element.name + ', '
      })
      return display.slice(0, -2)
    },
    activitiesDisplay (item) {
      let display = ''
      item.activities.forEach(element => {
        display += element.name + ', '
      })
      return display.slice(0, -2)
    },
    returnHeaders () {
      switch (this.source) {
        case 'activities':
          return this.activitiesHeaders
        case 'activity-groups':
          return this.groupsHeaders
        case 'activity-instances':
          return this.instantiationsHeaders
      }
    },
    inactivateActivity (item, source) {
      source = (source === undefined) ? this.source : source
      activities.inactivate(item.uid, source).then(resp => {
        this.fetchActivities()
      })
    },
    reactivateActivity (item, source) {
      source = (source === undefined) ? this.source : source
      activities.reactivate(item.uid, source).then(resp => {
        this.fetchActivities()
      })
    },
    deleteActivity (item, source) {
      source = (source === undefined) ? this.source : source
      activities.delete(item.uid, source).then(resp => {
        this.fetchActivities()
      })
    },
    approveActivity (item, source) {
      source = (source === undefined) ? this.source : source
      activities.approve(item.uid, source).then(resp => {
        this.fetchActivities()
      })
    },
    newActivityVersion (item, source) {
      source = (source === undefined) ? this.source : source
      activities.newVersion(item.uid, source).then(resp => {
        this.fetchActivities()
      })
    },
    showForm () {
      switch (this.source) {
        case 'activities':
          this.showActivityForm = true
          return
        case 'activity-groups':
          this.showGroupsForm = true
          return
        case 'activity-instances':
          this.showInstantiationsForm = true
      }
    },
    editActivity (item, source) {
      this.activeActivity = item
      if (source === 'activities') {
        this.showActivityForm = true
        return
      }
      switch (this.source) {
        case 'activities':
          this.showActivityForm = true
          return
        case 'activity-groups':
          this.showGroupsForm = true
          return
        case 'activity-instances':
          this.showInstantiationsForm = true
      }
    },
    getSubGroups ({ item }) {
      this.subgroups = []
      this.loading = true
      this.currentGroup = item.uid
      activities.getSubGroups(item.uid).then(resp => {
        this.subgroups = resp.data.items
        this.loading = false
      })
    },
    getSubgroupActivities ({ item }) {
      this.subgroupActivities = []
      this.subLoading = true
      this.currentSubGroup = item.uid
      activities.getSubGroupActivities(item.uid).then(resp => {
        this.subgroupActivities = resp.data.items
        this.subLoading = false
      })
    },
    closeForm () {
      this.showActivityForm = false
      this.showGroupsForm = false
      this.showInstantiationsForm = false
      this.activeActivity = null
      this.fetchActivities()
    }
  },
  mounted () {
    this.fetchActivities()
  }
}
</script>
