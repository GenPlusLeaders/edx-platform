import React from 'react';
import { Button } from '@edx/paragon';
import BlockBrowserContainer from 'BlockBrowser/components/BlockBrowser/BlockBrowserContainer';

function SkillAssessmentTableRows(props) {
    const {
        rowsData,
        deleteTableRows,
        skills,
        unitKeys,
        problem_types,
        handleSelectIntro,
        handleSelectOutro,
        handleSelectSkill,
        handleProblemType,
        handleIntroToggleDropdown,
        handleOutroToggleDropdown,
        hideIntroDropdown,
        hideOutroDropdown,
        onSelectBlock
    } = props;
    return(
        rowsData.map((data, index)=>{
            const {
                skill,
                start_unit,
                end_unit,
                question_number,
                problem_type,
                start_unit_location,
                end_unit_location,
                showIntroDropdown,
                showOutroDropdown
            } = data;

            let isLikert = false;
            problem_types.forEach(({name, value}) => {
              if(value === +problem_type && name === "LIKERT") {
                isLikert = true;
              }
            })

            return (
              <tr key={index}>
                <td>{question_number}</td>
                <td>
                    <select
                    value={start_unit}
                    onChange={(event) => handleSelectIntro(index, event)}
                    className="form-control"
                    id={"select-intro-" + index}
                    >
                    <option value="">Select Intro Unit</option>
                    {
                        unitKeys.map((unitKey, index) => (
                            <option key={index} value={unitKey}>{unitKey}</option>
                        ))
                    }
                    </select>
                    <div className="problem-browser">
                        <Button onClick={()=>handleIntroToggleDropdown(index)} label={gettext('Select Intro Problem')} />
                        {
                          start_unit_location && <div className="unit-label">{start_unit_location}</div>
                        }
                        {
                            showIntroDropdown && start_unit !== "" &&
                            <BlockBrowserContainer
                            onSelectBlock={(blockId) => {
                                onSelectBlock(blockId);
                                hideIntroDropdown(index, blockId);
                            }}
                            />
                        }
                    </div>
                </td>
                <td>
                  {
                    isLikert && (
                      <div>
                        <select
                            value={end_unit}
                            onChange={(event) => handleSelectOutro(index, event)}
                            className="form-control"
                            id={"select-outro-" + index}
                            >
                            <option value="">Select Outro Unit</option>
                            {
                                unitKeys.map((unitKey, index) => (
                                    <option key={index} value={unitKey}>{unitKey}</option>
                                ))
                            }
                        </select>
                        <div className="problem-browser">
                            <Button onClick={()=>handleOutroToggleDropdown(index)} label={gettext('Select Outro Problem')} />
                            {
                              end_unit_location && <div className="unit-label">{end_unit_location}</div>
                            }
                            {
                                showOutroDropdown && end_unit !== "" &&
                                <BlockBrowserContainer
                                onSelectBlock={(blockId) => {
                                    onSelectBlock(blockId);
                                    hideOutroDropdown(index, blockId);
                                }}
                                />
                            }
                        </div>
                      </div>
                    )
                  }
                </td>
                <td>
                    <select
                      value={problem_type || ''}
                      onChange={(event) => handleProblemType(index, event)}
                      className="form-control select-skill"
                      id={"select-ProblemType-" + index}
                    >
                    <option value="">Select Problem Type</option>
                    {
                        problem_types.map((problemType, index) => (
                            <option key={index} value={problemType.value}>{problemType.name}</option>
                        ))
                    }
                    </select>
                </td>
                <td>
                    <select
                      value={skill}
                      onChange={(event) => handleSelectSkill(index, event)}
                      className="form-control"
                      id={"select-skill-" + index}
                    >
                    <option value="">Select Skill</option>
                    {
                        skills.map((skillName, index) => (
                            <option key={index} value={skillName}>{skillName}</option>
                        ))
                    }
                    </select>
                </td>
                <td><button className="btn btn-outline-danger" onClick={()=>(deleteTableRows(index))}>x</button></td>
              </tr>
            )
        })
    )
}

export default SkillAssessmentTableRows;
