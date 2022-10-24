<template>
<div class="pt-4">
  <n-n-table
    :headers="headers"
    :items="criteria"
    hide-fixed-headers-switch
    :export-data-url="exportDataUrl"
    :export-data-url-params="exportDataUrlParams"
    >
    <template v-slot:afterSwitches>
      <div :title="$t('NNTableTooltips.reorder_content')">
        <v-switch
          v-model="sortMode"
          :label="$t('NNTable.reorder_content')"
          hide-details
          class="mr-6"
          />
      </div>
    </template>
    <template v-slot:actions>
      <v-btn
        data-cy="add-study-criteria"
        fab
        small
        color="primary"
        @click.stop="addCriteria"
        :title="$t('EligibilityCriteriaTable.add_criteria')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.name="{ item }">
      <template v-if="item.criteriaTemplate">
        <n-n-parameter-highlighter
          :name="item.criteriaTemplate.name"
          default-color="orange"
          />
      </template>
      <template v-else>
        <n-n-parameter-highlighter
          :name="item.criteria.name"
          :show-prefix-and-postfix="false"
          />
      </template>
    </template>
    <template v-slot:item.keyCriteria="{ item }">
      <v-checkbox
        v-model="item.keyCriteria"
        @change="updateKeyCriteria($event, item.studyCriteriaUid)"
        />
    </template>
    <template v-slot:item.guidanceText="{ item }">
      <template v-if="item.criteria">
        <span v-html="item.criteria.criteriaTemplate.guidanceText" />
      </template>
      <template v-else-if="item.criteriaTemplate">
        <span v-html="item.criteriaTemplate.guidanceText" />
      </template>
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate|date }}
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu
        :key="item.studyCriteriaUid"
        :actions="filterEditAction(item)"
        :item="item"
        :badge="actionsMenuBadge(item)"
        />
    </template>
    <template v-slot:body="props" v-if="criteria.length > 0 && sortMode">
      <draggable
        :list="props.items"
        tag="tbody"
        @change="onOrderChange($event)"
        >
        <tr
          v-for="(item, index) in props.items"
          :key="index"
          >
          <td v-if="props.showSelectBoxes">
            <v-checkbox
              :value="item.criteria.name"
              hide-details
              @change="props.select(!props.isSelected(item))"
              />
          </td>
          <td>
            <actions-menu
              :key="item.studyCriteriaUid"
              :actions="filterEditAction(item)"
              :item="item"
              :badge="actionsMenuBadge(item)"
              />
          </td>
          <td>
            <v-icon
              small
              v-if="sortMode"
              >
              mdi-sort
            </v-icon>
            {{ item.order }}
          </td>
          <td>
            <template v-if="item.criteriaTemplate">
              <n-n-parameter-highlighter
                :name="item.criteriaTemplate.name"
                default-color="orange"
                />
            </template>
            <template v-else>
              <n-n-parameter-highlighter
                :name="item.criteria.name"
                :show-prefix-and-postfix="false"
                />
            </template>
          </td>
          <td>
            <template v-if="item.criteriaTemplate">
              <span v-html="item.criteriaTemplate.guidanceText" />
            </template>
            <template v-else>
              <span v-html="item.criteria.criteriaTemplate.guidanceText" />
            </template>
          </td>
          <td>
            <v-checkbox
              v-model="item.keyCriteria"
              @change="updateKeyCriteria($event, item.studyCriteriaUid)"
              />
          </td>
          <td>
            {{ item.startDate|date }}
          </td>
          <td>
            {{ item.userInitials }}
          </td>
        </tr>
      </draggable>
    </template>
  </n-n-table>
  <v-dialog v-model="showForm"
            persistent
            fullscreen
            content-class="fullscreen-dialog"
            >
    <eligibility-criteria-form
      @close="closeForm"
      :criteria-type="criteriaType"
      class="fullscreen-dialog"
      @added="getStudyCriteria"
      />
  </v-dialog>
  <v-dialog
    v-model="showEditForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
    >
    <eligibility-criteria-edit-form
      :study-criteria="selectedStudyCriteria"
      @close="closeEditForm"
      @updated="getStudyCriteria"
      class="fullscreen-dialog"
      />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    max-width="1200px"
    >
    <history-table
      @close="closeHistory"
      :type="'studyCriteria'"
      :item="selectedStudyCriteria"
      :title-label="'Study Criteria'"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu'
import { bus } from '@/main'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import draggable from 'vuedraggable'
import EligibilityCriteriaEditForm from './EligibilityCriteriaEditForm'
import EligibilityCriteriaForm from './EligibilityCriteriaForm'
import HistoryTable from '@/components/library/HistoryTable'
import { mapGetters } from 'vuex'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import study from '@/api/study'

export default {
  props: {
    criteriaType: Object
  },
  components: {
    ActionsMenu,
    ConfirmDialog,
    draggable,
    EligibilityCriteriaEditForm,
    EligibilityCriteriaForm,
    HistoryTable,
    NNParameterHighlighter,
    NNTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-criteria`
    },
    exportDataUrlParams () {
      return {
        filters: JSON.stringify({ 'criteriaType.sponsorPreferredNameSentenceCase': { v: [this.criteriaType.sponsorPreferredNameSentenceCase] } })
      }
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editStudyCriteria
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteStudyCriteria
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory
        }
      ],
      criteria: [],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: '#', value: 'order', width: '5%' },
        { text: this.criteriaType.sponsorPreferredName, value: 'name', width: '30%' },
        { text: this.$t('EligibilityCriteriaTable.guidance_text'), value: 'guidanceText', width: '20%' },
        { text: this.$t('EligibilityCriteriaTable.key_criteria'), value: 'keyCriteria' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'userInitials' }
      ],
      selectedStudyCriteria: null,
      showEditForm: false,
      showForm: false,
      showHistory: false,
      sortMode: false
    }
  },
  methods: {
    actionsMenuBadge (item) {
      if (!item.criteria && item.criteriaTemplate.parameters.length > 0) {
        return {
          color: 'error',
          icon: 'mdi-exclamation'
        }
      }
      return undefined
    },
    filterEditAction (item) {
      if ((item.criteria && item.criteria.parameterValues.length > 0) || (item.criteriaTemplate && item.criteriaTemplate.parameters.length > 0)) {
        return this.actions
      } else {
        return this.actions.slice(1)
      }
    },
    addCriteria () {
      this.showForm = true
    },
    closeEditForm () {
      this.showEditForm = false
    },
    closeForm () {
      this.showForm = false
    },
    closeHistory () {
      this.selectedStudyCriteria = null
      this.showHistory = false
    },
    openHistory (studyCriteria) {
      this.selectedStudyCriteria = studyCriteria
      this.showHistory = true
    },
    editStudyCriteria (studyCriteria) {
      this.showEditForm = true
      this.selectedStudyCriteria = studyCriteria
    },
    async deleteStudyCriteria (studyCriteria) {
      const options = { type: 'warning' }
      let criterion = (studyCriteria.criteriaTemplate) ? studyCriteria.criteriaTemplate.name : studyCriteria.criteria.name

      criterion = criterion.replaceAll(/\[|\]/g, '')
      if (await this.$refs.confirm.open(this.$t('EligibilityCriteriaTable.confirm_delete', { criterion }), options)) {
        await study.deleteStudyCriteria(this.selectedStudy.uid, studyCriteria.studyCriteriaUid)
        this.getStudyCriteria()
        bus.$emit('notification', { msg: this.$t('EligibilityCriteriaTable.delete_success') })
      }
    },
    getStudyCriteria (sortByOrder) {
      study.getStudyCriteriaWithType(this.selectedStudy.uid, this.criteriaType).then(resp => {
        this.criteria = resp.data.items
        if (sortByOrder) {
          this.sortStudyCriteria()
        }
      })
    },
    onOrderChange (event) {
      const studyCriteria = event.moved.element
      const replacedStudyCriteria = this.criteria[event.moved.newIndex]
      study.updateStudyCriteriaOrder(this.selectedStudy.uid, studyCriteria.studyCriteriaUid, replacedStudyCriteria.order).then(resp => {
        this.getStudyCriteria()
      })
    },
    sortStudyCriteria () {
      this.criteria.sort((a, b) => {
        return a.order - b.order
      })
    },
    updateKeyCriteria (value, studyCriteriaUid) {
      study.updateStudyCriteriaKeyCriteria(this.selectedStudy.uid, studyCriteriaUid, value).then(resp => {
        this.getStudyCriteria()
      })
    }
  },
  mounted () {
    this.$store.dispatch('studiesGeneral/fetchTrialPhases')
    this.getStudyCriteria()
  },
  watch: {
    sortMode (value) {
      this.headers.forEach(header => {
        this.$set(header, 'sortable', !value)
      })
      this.sortStudyCriteria()
    }
  }
}
</script>
