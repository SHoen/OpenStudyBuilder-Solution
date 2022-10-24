<template>
<div>
  <v-row>
    <v-switch class="ml-6 mt-6" @change="(v) => expandAll(items, v)" v-if="!loading" :label="$t('CrfTree.expand_all')"/>
    <v-switch class="ml-3 mt-6" v-if="!loading" v-model="sortMode" :label="$t('CrfTree.reorder')"/>
  </v-row>
  <v-data-table
    ref="templatesTable"
    :headers="headers"
    item-key="uid"
    :options.sync="options"
    :server-items-length="total"
    :items="crfTreeData"
    export-data-url="concepts/odms/templates"
    show-expand
    light
    class="mt-5 tableMinWidth"
    :loading="loading"
    hide-default-header
    width="100%"
    :expanded="templatesExpand"
    sort-by="name"
    >
    <template v-slot:header="{ props: { headers } }">
      <thead>
        <tr>
          <th v-for="header in headers" v-bind:key="header.value">
            <span>{{ header.text }}</span>
          </th>
        </tr>
      </thead>
    </template>
    <template v-slot:item="{ item, expand, isExpanded }">
      <tr style="background-color: var(--v-dfltBackgroundLight1-base)">
        <td width="1%">
          <v-btn @click="expand(!isExpanded)" v-if="isExpanded" icon>
            <v-icon dark>
              mdi-chevron-up
            </v-icon>
          </v-btn>
          <v-btn @click="expand(!isExpanded)" v-else-if="!loading" icon>
            <v-icon dark>
              mdi-chevron-down
            </v-icon>
          </v-btn>
        </td>
        <td width="30%">
          <v-icon color="primary">mdi-alpha-t-circle</v-icon>
          {{ item.name }}
        </td>
        <td width="20%">{{ item.version }}</td>
        <td width="15%"><status-chip :status="item.status" /></td>
        <td width="10%"></td>
        <td width="10%"></td>
        <td width="10%">
          <v-menu
            offset-y
            >
            <template v-slot:activator="{ on, attrs }">
              <div>
                <v-btn
                  fab
                  dark
                  small
                  v-bind="attrs"
                  v-on="on"
                  color="success"
                  :title="$t('CrfTree.link_forms')"
                  :disabled="item.status === 'Final'"
                  >
                  <v-icon dark>
                    mdi-plus
                  </v-icon>
                </v-btn>
              </div>
            </template>
            <v-list>
              <v-list-item @click="openForm(item, 'forms')">
                <v-list-item-icon>
                  <v-icon>mdi-plus</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  {{ $t('CrfTree.link_existing')}}
                </v-list-item-content>
              </v-list-item>
              <v-list-item @click="openFormsForm(item)">
                <v-list-item-icon>
                  <v-icon>mdi-pencil</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  {{ $t('CrfTree.create_and_link')}}
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-menu>
        </td>
      </tr>
    </template>
    <template v-slot:expanded-item="{ headers, item }">
      <td :colspan="headers.length" class="pa-0">
        <v-data-table
          ref="formsTable"
          :headers="headers"
          :items="item.forms"
          item-key="uid"
          light
          hide-default-footer
          hide-default-header
          show-expand
          :expanded="formsExpand"
          sort-by="orderNumber"
          :key="tableKey"
          >
          <template v-slot:item="{ item, expand, isExpanded }">
            <tr style="background-color: var(--v-dfltBackgroundLight2-base)">
              <td width="1%">
                <v-btn @click="expand(!isExpanded)" v-if="isExpanded" icon>
                  <v-icon dark>
                    mdi-chevron-up
                  </v-icon>
                </v-btn>
                <v-btn @click="expand(!isExpanded), addToExpandArray(item)" v-else icon>
                  <v-icon dark>
                    mdi-chevron-down
                  </v-icon>
                </v-btn>
              </td>
              <td width="30%">
                <v-row>
                  <v-btn
                    class="mt-4 ml-3"
                    icon x-small
                    v-if="sortMode"
                    @click="reorderContent(item, -1)">
                    <v-icon>
                      mdi-arrow-up
                    </v-icon>
                  </v-btn>
                  <v-btn
                    class="mt-4"
                    icon
                    x-small
                    v-if="sortMode"
                    @click="reorderContent(item, 1)">
                    <v-icon>
                      mdi-arrow-down
                    </v-icon>
                  </v-btn>
                  <v-icon class="ml-6 mt-3" color="success">mdi-alpha-f-circle</v-icon>
                  <div class="mt-3 ml-1 mr-1">{{ item.name }}</div>
                </v-row>
              </td>
              <td width="20%">{{ item.version }}</td>
              <td width="15%"><status-chip :status="item.status" /></td>
              <td width="10%">
                <v-checkbox
                  false-value="No"
                  true-value="Yes"
                  v-model="item.repeating"
                  hide-details
                  disabled
                  class="ma-0 pa-0"
                  />
              </td>
              <td width="10%">
                <v-checkbox
                  false-value="No"
                  true-value="Yes"
                  v-model="item.mandatory"
                  hide-details
                  @change="updateMandatory(item)"
                  class="ma-0 pa-0"
                  />
              </td>
              <td width="10%">
                <v-menu
                  offset-y
                  >
                  <template v-slot:activator="{ on, attrs }">
                    <div>
                      <v-btn
                        fab
                        dark
                        small
                        v-bind="attrs"
                        v-on="on"
                        color="secondary"
                        :title="$t('CrfTree.link_item_groups')"
                        :disabled="item.status === 'Final'"
                        >
                        <v-icon dark>
                          mdi-plus
                        </v-icon>
                      </v-btn>
                    </div>
                  </template>
                  <v-list>
                    <v-list-item @click="openForm(item, 'item-groups')">
                      <v-list-item-icon>
                        <v-icon>mdi-plus</v-icon>
                      </v-list-item-icon>
                      <v-list-item-content>
                        {{ $t('CrfTree.link_existing')}}
                      </v-list-item-content>
                    </v-list-item>
                    <v-list-item @click="openItemGroupForm(item)">
                      <v-list-item-icon>
                        <v-icon>mdi-pencil</v-icon>
                      </v-list-item-icon>
                      <v-list-item-content>
                        {{ $t('CrfTree.create_and_link')}}
                      </v-list-item-content>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </td>
            </tr>
          </template>
          <template v-slot:expanded-item="{ headers, item }">
            <td :colspan="headers.length" class="pa-0">
              <v-data-table
                class="elevation-0"
                :headers="headers"
                :items="item.itemGroups"
                item-key="uid"
                light
                hide-default-footer
                hide-default-header
                show-expand
                :expanded="groupsExpand"
                sort-by="orderNumber"
                :key="tableKey"
                >
                <template v-slot:item="{ item, expand, isExpanded }">
                  <tr style="background-color: var(--v-dfltBackground-base)">
                    <td width="1%">
                      <v-btn @click="expand(!isExpanded)" v-if="isExpanded" icon>
                        <v-icon dark>
                          mdi-chevron-up
                        </v-icon>
                      </v-btn>
                      <v-btn @click="expand(!isExpanded), addToExpandArray(item)" v-else icon>
                        <v-icon dark>
                          mdi-chevron-down
                        </v-icon>
                      </v-btn>
                    </td>
                    <td width="30%" class="pl-0">
                      <v-row>
                        <v-btn
                          class="mt-4 ml-7"
                          icon x-small
                          v-if="sortMode"
                          @click="reorderContent(item, -1)">
                          <v-icon>
                            mdi-arrow-up
                          </v-icon>
                        </v-btn>
                        <v-btn
                          class="mt-4"
                          icon
                          x-small
                          v-if="sortMode"
                          @click="reorderContent(item, 1)">
                          <v-icon>
                            mdi-arrow-down
                          </v-icon>
                        </v-btn>
                        <div class="mt-3 ml-4"><actions-menu :actions="actions" :item="item"/></div>
                        <v-icon color="secondary">mdi-alpha-g-circle</v-icon>
                        <div class="mt-3 ml-1 mr-1">{{ item.name }}</div>
                        <v-tooltip bottom v-if="checkIfConditionExist(item)">
                          <template v-slot:activator="{ on, attrs }">
                            <v-icon
                              v-bind="attrs"
                              v-on="on">
                              mdi-alert-circle-check-outline
                            </v-icon>
                          </template>
                          <span>{{ $t('CrfTree.condition_applied') }}</span>
                        </v-tooltip>
                      </v-row>
                    </td>
                    <td width="20%">{{ item.version }}</td>
                    <td width="15%"><status-chip :status="item.status" /></td>
                    <td width="10%">
                      <v-checkbox
                        false-value="No"
                        true-value="Yes"
                        v-model="item.repeating"
                        hide-details
                        disabled
                        class="ma-0 pa-0"
                        />
                    </td>
                    <td width="10%">
                      <v-checkbox
                        false-value="No"
                        true-value="Yes"
                        v-model="item.mandatory"
                        hide-details
                        @change="updateMandatory(item)"
                        class="ma-0 pa-0"
                        />
                    </td>
                    <td width="10%">
                      <v-menu
                        offset-y
                        >
                        <template v-slot:activator="{ on, attrs }">
                          <div>
                            <v-btn
                              fab
                              dark
                              small
                              v-bind="attrs"
                              v-on="on"
                              color="red"
                              :title="$t('CrfTree.link_items')"
                              :disabled="item.status === 'Final'"
                              >
                              <v-icon dark>
                                mdi-plus
                              </v-icon>
                            </v-btn>
                          </div>
                        </template>
                        <v-list>
                          <v-list-item @click="openForm(item, 'items')">
                            <v-list-item-icon>
                              <v-icon>mdi-plus</v-icon>
                            </v-list-item-icon>
                            <v-list-item-content>
                              {{ $t('CrfTree.link_existing')}}
                            </v-list-item-content>
                          </v-list-item>
                          <v-list-item @click="openItemForm(item)">
                            <v-list-item-icon>
                              <v-icon>mdi-pencil</v-icon>
                            </v-list-item-icon>
                            <v-list-item-content>
                              {{ $t('CrfTree.create_and_link')}}
                            </v-list-item-content>
                          </v-list-item>
                        </v-list>
                      </v-menu>
                    </td>
                  </tr>
                </template>
                <template v-slot:expanded-item="{ headers, item }">
                  <td :colspan="headers.length" class="pa-0">
                    <v-data-table
                      class="elevation-0"
                      :headers="headers"
                      :items="item.items"
                      item-key="uid"
                      sort-by="orderNumber"
                      light
                      hide-default-footer
                      hide-default-header
                      :key="tableKey"
                      >
                      <template v-slot:item="{ item }">
                        <tr>
                          <td width="1%">
                            <v-btn icon>
                            </v-btn>
                          </td>
                          <td width="30%" class="pl-0">
                            <v-row>
                              <v-btn
                                class="mt-4 ml-7"
                                icon x-small
                                v-if="sortMode"
                                @click="reorderContent(item, -1)">
                                <v-icon>
                                  mdi-arrow-up
                                </v-icon>
                              </v-btn>
                              <v-btn
                                class="mt-4"
                                icon
                                x-small
                                v-if="sortMode"
                                @click="reorderContent(item, 1)">
                                <v-icon>
                                  mdi-arrow-down
                                </v-icon>
                              </v-btn>
                              <div class="mt-3 ml-8"><actions-menu :actions="actions" :item="item"/></div>
                              <v-icon color="error">mdi-alpha-i-circle</v-icon>
                              <div class="mt-3 ml-1 mr-1">{{ item.name }}</div>
                              <v-tooltip bottom v-if="checkIfConditionExist(item)">
                                <template v-slot:activator="{ on, attrs }">
                                  <v-icon
                                    v-bind="attrs"
                                    v-on="on">
                                    mdi-alert-circle-check-outline
                                  </v-icon>
                                </template>
                                <span>{{ $t('CrfTree.condition_applied') }}</span>
                              </v-tooltip>
                            </v-row>
                          </td>
                          <td width="20%">{{ item.version }}</td>
                          <td width="15%"><status-chip :status="item.status" /></td>
                          <td width="10%"></td>
                          <td width="10%">
                            <v-checkbox
                              false-value="No"
                              true-value="Yes"
                              v-model="item.mandatory"
                              hide-details
                              @change="updateMandatory(item)"
                              />
                          </td>
                          <td width="10%"></td>
                        </tr>
                      </template>
                    </v-data-table>
                  </td>
                </template>
              </v-data-table>
            </td>
          </template>
        </v-data-table>
      </td>
    </template>
  </v-data-table>
  <crf-link-form
    :open="showForm"
    @close="closeForm"
    :itemToLink="itemToLink"
    :itemsType="linkedItemsType"
    />
  <v-dialog
    v-model="conditionForm"
    persistent
    content-class="fullscreen-dialog"
    >
    <crf-condition-form
      :itemToLink="itemToLink"
      @close="closeConditionForm"
      @cancel="cancelConditionForm"
      :crfForms="forms"
      :crfGroup="currentItemGroup"
      :crfGroups="itemGroups"
      :crfItems="items"/>
  </v-dialog>
  <v-dialog
    v-model="showFormsForm"
    persistent
    content-class="fullscreen-dialog"
    >
    <crf-form-form
      @close="closeFormsForm"
      @linkForm="linkForm"
      :editItem="{}"
      class="fullscreen-dialog"
      />
  </v-dialog>
  <v-dialog
    v-model="showItemGroupForm"
    persistent
    content-class="fullscreen-dialog"
    >
    <crf-item-group-form
      @close="closeItemGroupForm"
      @linkGroup="linkGroup"
      :editItem="{}"
      class="fullscreen-dialog"
      />
  </v-dialog>
  <v-dialog
    v-model="showItemForm"
    persistent
    content-class="fullscreen-dialog"
    >
    <crf-item-form
      @close="closeItemForm"
      @linkItem="linkItem"
      :editItem="{}"
      class="fullscreen-dialog"
      />
  </v-dialog>
</div>
</template>

<script>
import crfs from '@/api/crfs'
import StatusChip from '@/components/tools/StatusChip'
import CrfLinkForm from '@/components/library/CrfLinkForm'
import CrfConditionForm from '@/components/library/CrfConditionForm'
import ActionsMenu from '@/components/tools/ActionsMenu'
import CrfItemGroupForm from '@/components/library/CrfItemGroupForm'
import CrfFormForm from '@/components/library/CrfFormForm'
import CrfItemForm from '@/components/library/CrfItemForm'
import constants from '@/constants/parameters'

export default {
  components: {
    ActionsMenu,
    StatusChip,
    CrfLinkForm,
    CrfConditionForm,
    CrfItemGroupForm,
    CrfFormForm,
    CrfItemForm
  },
  props: {
    source: String,
    refresh: String
  },
  data () {
    return {
      crfTreeData: [],
      headers: [
        { text: this.$t('CrfTree.items_for_linking'), value: 'name' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('CrfTree.repeating'), value: 'repeating' },
        { text: this.$t('CrfTree.mandatory'), value: 'mandatory' },
        { text: this.$t('CrfTree.link'), value: 'link' }
      ],
      options: {},
      total: 0,
      templates: [],
      forms: [],
      loading: false,
      showForm: false,
      itemToLink: {},
      linkedItemsType: '',
      itemGroups: [],
      items: [],
      currentTemplate: {},
      currentForm: {},
      currentItemGroup: {},
      conditionForm: false,
      actions: [
        {
          label: this.$t('CrfTree.edit_condition'),
          icon: 'mdi-pencil',
          click: this.openConditionForm,
          condition: (item) => this.checkIfConditionExist(item)
        },
        {
          label: this.$t('CrfTree.set_condition'),
          icon: 'mdi-pencil',
          click: this.openConditionForm,
          condition: (item) => !this.checkIfConditionExist(item)
        },
        {
          label: this.$t('CrfTree.delete_condition'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => this.checkIfConditionExist(item),
          click: this.deleteCondition
        }
      ],
      templatesExpand: [],
      formsExpand: [],
      groupsExpand: [],
      showFormsForm: false,
      showItemGroupForm: false,
      showItemForm: false,
      sortMode: false,
      tableKey: 0
    }
  },
  methods: {
    addToExpandArray (item) {
      if (item.activityGroups) {
        this.formsExpand.push(item)
      } else {
        this.groupsExpand.push(item)
      }
    },
    reorderContent (item, direction) {
      if (item.orderNumber === 0 && direction === -1) {
        return
      }
      const movedItemNewOrder = item.orderNumber + direction
      if (item.parentGroupUid) {
        const group = this.itemGroups.find(group => group.uid === item.parentGroupUid)
        if (direction === 1) {
          this.$set(group.items.find(el => el.orderNumber === movedItemNewOrder), 'orderNumber', (group.items.find(el => el.orderNumber === movedItemNewOrder).orderNumber - 1))
          item.orderNumber = movedItemNewOrder
        } else {
          this.$set(group.items.find(el => el.orderNumber === movedItemNewOrder), 'orderNumber', (group.items.find(el => el.orderNumber === movedItemNewOrder).orderNumber + 1))
          item.orderNumber = movedItemNewOrder
        }
        crfs.addItemsToItemGroup(group.items, group.uid, true).then(resp => {
        })
      } else if (item.parentFormUid) {
        const form = this.forms.find(form => form.uid === item.parentFormUid)
        if (direction === 1) {
          this.$set(form.itemGroups.find(el => el.orderNumber === movedItemNewOrder), 'orderNumber', (form.itemGroups.find(el => el.orderNumber === movedItemNewOrder).orderNumber - 1))
          item.orderNumber = movedItemNewOrder
        } else {
          this.$set(form.itemGroups.find(el => el.orderNumber === movedItemNewOrder), 'orderNumber', (form.itemGroups.find(el => el.orderNumber === movedItemNewOrder).orderNumber + 1))
          item.orderNumber = movedItemNewOrder
        }
        crfs.addItemGroupsToForm(form.itemGroups, form.uid, true).then(resp => {
        })
      } else if (item.parentTemplateUid) {
        const template = this.templates.find(template => template.uid === item.parentTemplateUid)
        if (direction === 1) {
          this.$set(template.forms.find(el => el.orderNumber === movedItemNewOrder), 'orderNumber', (template.forms.find(el => el.orderNumber === movedItemNewOrder).orderNumber - 1))
          item.orderNumber = movedItemNewOrder
        } else {
          this.$set(template.forms.find(el => el.orderNumber === movedItemNewOrder), 'orderNumber', (template.forms.find(el => el.orderNumber === movedItemNewOrder).orderNumber + 1))
          item.orderNumber = movedItemNewOrder
        }
        crfs.addFormsToTemplate(template.forms, template.uid, true).then(resp => {
        })
      }
      this.tableKey += 1
    },
    expandAll (items, status) {
      if (status) {
        this.templatesExpand = this.templates
        this.formsExpand = this.forms
        this.groupsExpand = this.itemGroups
      } else {
        this.templatesExpand = []
        this.formsExpand = []
        this.groupsExpand = []
      }
    },
    checkIfConditionExist (item) {
      return (item.collectionExceptionConditionOid && item.collectionExceptionConditionOid !== 'null' && item.collectionExceptionConditionOid !== 'none')
    },
    openConditionForm (item) {
      this.itemToLink = item
      this.conditionForm = true
    },
    closeConditionForm () {
      this.itemToLink = {}
      this.conditionForm = false
      this.getCrfData()
    },
    cancelConditionForm () {
      this.itemToLink = {}
      this.conditionForm = false
    },
    openFormsForm (item) {
      this.itemToLink = item
      this.showFormsForm = true
    },
    closeFormsForm () {
      this.showFormsForm = false
      this.itemToLink = {}
    },
    openItemGroupForm (item) {
      this.itemToLink = item
      this.showItemGroupForm = true
    },
    closeItemGroupForm () {
      this.showItemGroupForm = false
      this.itemToLink = {}
    },
    openItemForm (item) {
      this.itemToLink = item
      this.showItemForm = true
    },
    closeItemForm () {
      this.showItemForm = false
      this.itemToLink = {}
    },
    linkForm (form) {
      const payload = [{
        uid: form.data.uid,
        orderNumber: this.itemToLink.forms.length,
        mandatory: false,
        collectionExceptionConditionOid: null
      }]
      crfs.addFormsToTemplate(payload, this.itemToLink.uid, false).then(resp => {
        this.getCrfData()
      })
    },
    linkGroup (group) {
      const payload = [{
        uid: group.data.uid,
        orderNumber: this.itemToLink.itemGroups.length,
        mandatory: false,
        collectionExceptionConditionOid: null
      }]
      crfs.addItemGroupsToForm(payload, this.itemToLink.uid, false).then(resp => {
        this.getCrfData()
      })
    },
    linkItem (item) {
      const payload = [{
        uid: item.data.uid,
        orderNumber: this.itemToLink.items.length,
        mandatory: false,
        collectionExceptionConditionOid: null,
        keySequence: constants.NULL,
        methodOid: constants.NULL,
        imputationMethodOid: constants.NULL,
        role: constants.NULL,
        roleCodelistOid: constants.NULL,
        dataEntryRequired: 'No',
        sdv: 'No'
      }]
      crfs.addItemsToItemGroup(payload, this.itemToLink.uid, false).then(resp => {
        this.getCrfData()
      })
    },
    deleteCondition (item) {
      const data = {}
      data.filters = `{"oid":{ "v": ["${item.collectionExceptionConditionOid}"], "op": "co" }}`
      crfs.getConditionByOid(data).then(resp => {
        crfs.deleteCondition(resp.data.items[0].uid).then(resp => {
          this.getCrfData()
        })
      })
    },
    async getCrfData (sort) {
      this.loading = true
      this.crfTreeData = []
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      await crfs.get('templates', { params }).then((resp) => {
        this.templates = resp.data.items
        this.total = resp.data.total
      })
      delete params.pageSize
      await crfs.get('forms', { params }).then((resp) => {
        this.forms = resp.data.items
      })
      await crfs.get('item-groups', { params }).then((resp) => {
        this.itemGroups = resp.data.items
      })
      await crfs.get('items', { params }).then((resp) => {
        this.items = resp.data.items
      })
      this.itemGroups.forEach((group, groupIndex) => {
        group.items.forEach((item, itemIndex) => {
          const mergedGroupItem = { ...this.itemGroups[groupIndex].items[itemIndex], ...this.items.find(i => i.uid === item.uid) }
          this.itemGroups[groupIndex].items[itemIndex] = Object.assign({}, mergedGroupItem)
          this.$set(this.itemGroups[groupIndex].items[itemIndex], 'parentGroupUid', group.uid)
        })
      })
      this.forms.forEach((form, formIndex) => {
        form.itemGroups.forEach((group, groupIndex) => {
          const mergedFormGroup = { ...this.forms[formIndex].itemGroups[groupIndex], ...this.itemGroups.find(g => g.uid === group.uid) }
          this.forms[formIndex].itemGroups[groupIndex] = Object.assign({}, mergedFormGroup)
          this.$set(this.forms[formIndex].itemGroups[groupIndex], 'parentFormUid', form.uid)
        })
      })
      this.templates.forEach((template, templateIndex) => {
        template.forms.forEach((form, formIndex) => {
          const mergedTemplateForm = { ...this.templates[templateIndex].forms[formIndex], ...this.forms.find(f => f.uid === form.uid) }
          this.templates[templateIndex].forms[formIndex] = Object.assign({}, mergedTemplateForm)
          this.$set(this.templates[templateIndex].forms[formIndex], 'parentTemplateUid', template.uid)
        })
      })
      this.crfTreeData = this.templates
      this.loading = false
    },
    openForm (item, type) {
      this.linkedItemsType = type
      this.itemToLink = item
      this.showForm = true
    },
    closeForm () {
      this.showForm = false
      this.getCrfData()
    },
    updateMandatory (item) {
      const payload = [{
        uid: item.uid,
        orderNumber: item.orderNumber,
        mandatory: item.mandatory === 'Yes',
        collectionExceptionConditionOid: item.collectionExceptionConditionOid,
        keySequence: item.keySequence,
        methodOid: item.methodOid,
        imputationMethodOid: item.imputationMethodOid,
        role: item.role,
        roleCodelistOid: item.roleCodelistOid,
        dataEntryRequired: item.dataEntryRequired === 'No' ? item.dataEntryRequired = false : item.dataEntryRequired = true,
        sdv: item.sdv
      }]
      if (item.parentFormUid) {
        crfs.addItemGroupsToForm(payload, item.parentFormUid, false)
      } else if (item.parentGroupUid) {
        crfs.addItemsToItemGroup(payload, item.parentGroupUid, false)
      } else {
        crfs.addFormsToTemplate(payload, item.parentTemplateUid, false)
      }
    }
  },
  watch: {
    options () {
      this.getCrfData()
    }
  }
}
</script>
<style scoped>
.tableMinWidth {
  min-width: 1440px !important;
}
.templates {
  background-color: var(--v-dfltBackgroundLight1-base);

}
.group {
  background-color: var(--v-dfltBackgroundLight2-base);
}
</style>
